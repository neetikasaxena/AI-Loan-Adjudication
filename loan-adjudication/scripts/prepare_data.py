"""Generate, label, split and tokenize the synthetic loan-application dataset.

Outputs (data/processed/):
  applications.jsonl            all labelled records (single free-text narrative each)
  train.jsonl / val.jsonl       stratified split (by decision)
  dialogues_{train,val}.jsonl   the same applications as multi-turn intake chats
  sft_{train,val}.jsonl         chat-format supervised examples, single-turn and dialogue, identity-masked
  tokenized_{train,val}.jsonl   input_ids / attention_mask / labels, padded to a fixed length
  prep_stats.json               label mix, scenario mix, token length stats
"""

from __future__ import annotations

import argparse
import json
import math
import random
import statistics
from collections import Counter, defaultdict
from pathlib import Path

from loan_adjudication import DEFAULT_RULES_PATH, PROJECT_ROOT
from loan_adjudication.explainer import LLMExplainer, TemplateExplainer
from loan_adjudication.llm_client import LLMClient
from loan_adjudication.rules_engine import Adjudication, RulesEngine
from loan_adjudication.synth import generate_dataset, rerender, to_dialogue_record

TASK_SINGLE = (
    "You adjudicate personal loan applications under credit policy v{version}. Extract the applicant's facts, "
    "apply every rule, and return JSON with keys: extracted_application, decision, failed_rules, reasoning."
)
TASK_DIALOGUE = (
    "You are a personal loan intake assistant applying credit policy v{version}. Ask for each fact the policy "
    "needs, one question at a time, and follow up once if the applicant does not answer. After the last answer, "
    "return JSON with keys: extracted_application, decision, failed_rules, reasoning."
)

def system_prompt(task: str, engine: RulesEngine, policy: str) -> str:
    text = task.format(version=engine.version)
    return f"{text}\n\n{engine.render_for_prompt()}" if policy == "full" else text

def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")

def label(records: list[dict], engine: RulesEngine) -> None:
    for rec in records:
        adj = engine.evaluate(rec["truth"])
        rec["label"] = adj.decision
        rec["failed_rule_ids"] = [r.rule.id for r in adj.failed]
        rec["missing_rule_ids"] = [r.rule.id for r in adj.missing]

def stratified_split(records: list[dict], val_frac: float, seed: int) -> tuple[list[dict], list[dict]]:
    by_label: dict[str, list[dict]] = defaultdict(list)
    for rec in records:
        by_label[rec["label"]].append(rec)
    rng = random.Random(seed)
    train, val = [], []
    for group in by_label.values():
        rng.shuffle(group)
        cut = round(len(group) * val_frac)
        val += group[:cut]
        train += group[cut:]
    key = lambda r: r["application_id"]  # noqa: E731
    return sorted(train, key=key), sorted(val, key=key)

def make_reasoner(mode: str, engine: RulesEngine):
    """Returns f(adjudication, seed) -> applicant-facing reasoning used as the training target."""
    template = TemplateExplainer()
    if mode == "template":
        return lambda adj, seed: template.reasoning(adj, variant=seed)
    client = LLMClient.from_env()
    if client is None:
        raise SystemExit("--reasoning llm requires LLM_BASE_URL (see .env.example)")
    llm = LLMExplainer(client, engine)

    def reason(adj: Adjudication, seed: int) -> str:
        explanation = llm.explain(adj)
        # Only guardrail-approved LLM text becomes a target; otherwise use a template paraphrase.
        return explanation.reasoning if explanation.source == "llm" else template.reasoning(adj, variant=seed)

    return reason

def to_sft(pairs: list[tuple[dict, dict]], engine: RulesEngine, policy: str, reason) -> list[dict]:
    single_system = system_prompt(TASK_SINGLE, engine, policy)
    dialogue_system = system_prompt(TASK_DIALOGUE, engine, policy)
    examples = []
    for rec, dialogue in pairs:
        adj = engine.evaluate(rec["truth"])
        answer = json.dumps({
            "extracted_application": rec["truth"],
            "decision": adj.decision,
            "failed_rules": adj.issue_ids,
            "reasoning": reason(adj, rec["render_seed"]),
        })
        examples.append({
            "application_id": rec["application_id"],
            "format": "single_turn",
            "messages": [
                {"role": "system", "content": single_system},
                {"role": "user", "content": rec["narrative_masked"]},
                {"role": "assistant", "content": answer},
            ],
        })
        examples.append({
            "application_id": rec["application_id"],
            "format": "dialogue",
            "messages": [{"role": "system", "content": dialogue_system}, *dialogue["messages_masked"],
                         {"role": "assistant", "content": answer}],
        })
    return examples

ROLE_TOKENS = {"system": "<|system|>", "user": "<|user|>", "assistant": "<|assistant|>"}

def render_prompt(messages: list[dict], tokenizer) -> str:
    if tokenizer.chat_template:
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    body = "".join(f"{ROLE_TOKENS[m['role']]}{m['content']}{tokenizer.eos_token}" for m in messages)
    return f"{tokenizer.bos_token or ''}{body}{ROLE_TOKENS['assistant']}"

def encode(example: dict, tokenizer) -> tuple[list[int], list[int]]:
    """Loss is computed on every assistant turn; system/user tokens are masked with -100."""
    messages = example["messages"]
    ids: list[int] = []
    labels: list[int] = []
    for i, message in enumerate(messages):
        if message["role"] != "assistant":
            continue
        # Re-render the conversation so far; it extends the previous ids with the new non-assistant turns.
        prefix = tokenizer(render_prompt(messages[:i], tokenizer), add_special_tokens=False)["input_ids"]
        labels = (labels + [-100] * len(prefix))[: len(prefix)]
        target = tokenizer(message["content"], add_special_tokens=False)["input_ids"] + [tokenizer.eos_token_id]
        ids = prefix + target
        labels = labels + target
    return ids, labels

def tokenize(examples: list[dict], tokenizer, max_length: int) -> tuple[list[dict], int]:
    rows, truncated = [], 0
    for ex in examples:
        ids, labels = encode(ex, tokenizer)
        if len(ids) > max_length:
            truncated += 1
            ids, labels = ids[:max_length], labels[:max_length]
        pad = max_length - len(ids)
        rows.append({
            "application_id": ex["application_id"],
            "format": ex["format"],
            "input_ids": ids + [tokenizer.pad_token_id] * pad,
            "attention_mask": [1] * len(ids) + [0] * pad,
            "labels": labels + [-100] * pad,
        })
    return rows, truncated

def load_tokenizer(name: str):
    try:
        from transformers import AutoTokenizer
    except ImportError:
        print("transformers not installed; skipping tokenization (pip install -e '.[tokenize]').")
        return None
    try:
        tokenizer = AutoTokenizer.from_pretrained(name)
    except Exception as exc:  # network/proxy/auth failures surface as many exception types
        print(f"Could not load tokenizer {name!r} ({exc.__class__.__name__}: {exc}); skipping tokenization.")
        return None
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    # Base models without a chat template get explicit role markers as atomic special tokens.
    if not tokenizer.chat_template:
        tokenizer.add_special_tokens({"additional_special_tokens": list(ROLE_TOKENS.values())})
    return tokenizer

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--n", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--val-frac", type=float, default=0.2)
    parser.add_argument("--rules", default=str(DEFAULT_RULES_PATH))
    parser.add_argument("--out", default=str(PROJECT_ROOT / "data" / "processed"))
    parser.add_argument("--tokenizer", default="Qwen/Qwen2.5-0.5B-Instruct", help="HF tokenizer id, or 'none' to skip")
    parser.add_argument("--max-length", type=int, default=0, help="0 = longest training example rounded up to 64")
    parser.add_argument("--policy-in-prompt", choices=["compact", "full"], default="compact",
                        help="compact: short task instruction only (policy is learned); full: embed every rule")
    parser.add_argument("--reasoning", choices=["template", "llm"], default="template",
                        help="Source of reasoning targets: varied templates, or guardrail-checked LLM letters")

    parser.add_argument("--wording-split", choices=["heldout", "shared"], default="heldout",
                        help="heldout: validation text uses phrasings never seen in training; shared: same pool")
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    engine = RulesEngine.from_file(args.rules)

    records = generate_dataset(args.n, seed=args.seed)
    label(records, engine)
    train, val = stratified_split(records, args.val_frac, args.seed)
    if args.wording_split == "heldout":
        train, val = [rerender(r, "train") for r in train], [rerender(r, "val") for r in val]
        records = sorted(train + val, key=lambda r: r["application_id"])
    dlg_train, dlg_val = [to_dialogue_record(r) for r in train], [to_dialogue_record(r) for r in val]
    write_jsonl(out / "applications.jsonl", records)
    write_jsonl(out / "train.jsonl", train)
    write_jsonl(out / "val.jsonl", val)
    write_jsonl(out / "dialogues_train.jsonl", dlg_train)
    write_jsonl(out / "dialogues_val.jsonl", dlg_val)

    reason = make_reasoner(args.reasoning, engine)
    sft_train = to_sft(list(zip(train, dlg_train)), engine, args.policy_in_prompt, reason)
    sft_val = to_sft(list(zip(val, dlg_val)), engine, args.policy_in_prompt, reason)
    write_jsonl(out / "sft_train.jsonl", sft_train)
    write_jsonl(out / "sft_val.jsonl", sft_val)

    stats: dict = {
        "n_total": len(records),
        "wording_split": args.wording_split,
        "label_mix": {"train": Counter(r["label"] for r in train), "val": Counter(r["label"] for r in val)},
        "scenario_mix": Counter(r["scenario"] for r in records),
        "rule_failure_counts": Counter(i for r in records for i in r["failed_rule_ids"] + r["missing_rule_ids"]),
        "sft": {"train": Counter(e["format"] for e in sft_train), "val": Counter(e["format"] for e in sft_val),
                "policy_in_prompt": args.policy_in_prompt, "reasoning": args.reasoning,
                "distinct_reasoning_openers": len({json.loads(e["messages"][-1]["content"])["reasoning"].split(".")[0]
                                                   for e in sft_train})},
        "dialogue_turns": {"mean": round(statistics.mean(len(d["messages"]) for d in dlg_train), 1),
                           "max": max(len(d["messages"]) for d in dlg_train)},
    }

    tokenizer = None if args.tokenizer.lower() == "none" else load_tokenizer(args.tokenizer)
    if tokenizer is not None:
        lengths = {fmt: [len(encode(ex, tokenizer)[0]) for ex in sft_train if ex["format"] == fmt]
                   for fmt in ("single_turn", "dialogue")}
        longest = max(max(v) for v in lengths.values())
        max_length = args.max_length or math.ceil(longest / 64) * 64
        tok_train, trunc_train = tokenize(sft_train, tokenizer, max_length)
        tok_val, trunc_val = tokenize(sft_val, tokenizer, max_length)
        write_jsonl(out / "tokenized_train.jsonl", tok_train)
        write_jsonl(out / "tokenized_val.jsonl", tok_val)
        stats["tokenization"] = {
            "tokenizer": args.tokenizer,
            "max_length": max_length,
            "train_length": {fmt: {"min": min(v), "mean": round(statistics.mean(v), 1),
                                   "p95": sorted(v)[int(0.95 * len(v)) - 1], "max": max(v)}
                             for fmt, v in lengths.items()},
            "system_prompt_tokens": len(tokenizer(sft_train[0]["messages"][0]["content"])["input_ids"]),
            "supervised_token_share": round(
                sum(sum(l != -100 for l in row["labels"]) for row in tok_train)
                / sum(sum(row["attention_mask"]) for row in tok_train), 3),
            "truncated": {"train": trunc_train, "val": trunc_val},
            "pad_token": tokenizer.pad_token,
            "eos_token": tokenizer.eos_token,
            "added_special_tokens": [] if tokenizer.chat_template else list(ROLE_TOKENS.values()),
            "vocab_size_after_additions": len(tokenizer),
        }

    (out / "prep_stats.json").write_text(json.dumps(stats, indent=2))
    print(json.dumps(stats, indent=2))
    print(f"\nWrote {len(train)} train / {len(val)} val records to {out}")

if __name__ == "__main__":
    main()
