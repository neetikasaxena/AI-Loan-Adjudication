"""Evaluate the adjudication pipeline on the validation split.

Reports extraction accuracy, decision metrics, rule-level agreement, explanation guardrails, fairness
(approval-rate parity, error-rate parity, counterfactual identity swaps) and the learned baselines.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

from loan_adjudication import PROJECT_ROOT
from loan_adjudication.explainer import PROTECTED_TERMS
from loan_adjudication.pipeline import Adjudicator, build_adjudicator
from loan_adjudication.schema import iter_fields
from loan_adjudication.synth import counterfactual_narrative

LABELS = ["APPROVE", "FLAG_REVIEW", "REJECT"]
BASELINES = ("tfidf_lr", "tfidf_lr_cv", "tree_structured")
FAIRNESS_ATTRS = ("gender", "ethnicity", "region")
NUMERIC_TOLERANCE = 0.05

def load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line]

def values_match(truth, pred) -> bool:
    if truth is None or pred is None or isinstance(truth, (bool, str)):
        return truth == pred
    return abs(float(truth) - float(pred)) <= NUMERIC_TOLERANCE

def bootstrap_ci(y_true: list[str], y_pred: list[str], n_boot: int = 1000, seed: int = 0) -> list[float]:
    hits = np.array([t == p for t, p in zip(y_true, y_pred)], dtype=float)
    rng = np.random.default_rng(seed)
    means = hits[rng.integers(0, len(hits), size=(n_boot, len(hits)))].mean(axis=1)
    return [round(float(np.percentile(means, 2.5)), 4), round(float(np.percentile(means, 97.5)), 4)]

def decision_metrics(y_true: list[str], y_pred: list[str]) -> dict:
    report = classification_report(y_true, y_pred, labels=LABELS, output_dict=True, zero_division=0)
    false_approvals = sum(t != "APPROVE" and p == "APPROVE" for t, p in zip(y_true, y_pred))
    return {
        "accuracy": round(accuracy_score(y_true, y_pred), 4),
        "accuracy_95ci": bootstrap_ci(y_true, y_pred),
        "macro_f1": round(f1_score(y_true, y_pred, labels=LABELS, average="macro", zero_division=0), 4),
        "reject_recall": round(report["REJECT"]["recall"], 4),
        "false_approvals": false_approvals,
        "per_class": {k: {m: round(v, 4) for m, v in report[k].items()} for k in LABELS},
        "confusion_matrix": {"labels": LABELS, "matrix": confusion_matrix(y_true, y_pred, labels=LABELS).tolist()},
    }

def extraction_metrics(records: list[dict], preds: list[dict]) -> dict:
    per_field: dict[str, list[bool]] = defaultdict(list)
    all_exact = []
    for rec, pred in zip(records, preds):
        truth_fields = dict(iter_fields(rec["truth"]))
        pred_fields = dict(iter_fields(pred["extracted_application"]))
        ok = [values_match(truth_fields[k], pred_fields[k]) for k in truth_fields]
        for key, hit in zip(truth_fields, ok):
            per_field[key].append(hit)
        all_exact.append(all(ok))
    return {
        "all_fields_exact": round(sum(all_exact) / len(all_exact), 4),
        "per_field_accuracy": {k: round(sum(v) / len(v), 4) for k, v in per_field.items()},
        "sources": Counter(p["extraction_source"] for p in preds),
    }

def explanation_metrics(preds: list[dict]) -> dict:
    words = [len(p["reasoning"].split()) for p in preds]
    issues = Counter(i.split(":")[0] for p in preds for i in p["guardrail_issues"])
    return {
        "sources": Counter(p["explanation_source"] for p in preds),
        "guardrail_issue_counts": issues,
        "protected_term_leaks_in_final_output": sum(bool(PROTECTED_TERMS.search(p["reasoning"])) for p in preds),
        "mean_words": round(sum(words) / len(words), 1),
    }

def fairness_metrics(records: list[dict], preds: list[dict]) -> dict:
    out = {}
    for attr in FAIRNESS_ATTRS:
        groups: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for rec, pred in zip(records, preds):
            groups[rec["identity"][attr]].append((rec["label"], pred["decision"]))
        table = {}
        for group, pairs in sorted(groups.items()):
            n = len(pairs)
            table[group] = {
                "n": n,
                "truth_approval_rate": round(sum(t == "APPROVE" for t, _ in pairs) / n, 4),
                "pred_approval_rate": round(sum(p == "APPROVE" for _, p in pairs) / n, 4),
                "error_rate": round(sum(t != p for t, p in pairs) / n, 4),
            }

        def ratio(key: str) -> float:
            rates = [g[key] for g in table.values()]
            return round(min(rates) / max(rates), 4) if max(rates) else 1.0

        out[attr] = {
            "groups": table,
            "pred_disparate_impact": ratio("pred_approval_rate"),
            "truth_disparate_impact": ratio("truth_approval_rate"),
            "error_rate_gap": round(max(g["error_rate"] for g in table.values()) - min(g["error_rate"] for g in table.values()), 4),
        }
        out[attr]["four_fifths_rule_pass"] = out[attr]["pred_disparate_impact"] >= 0.8
    return out

def counterfactual_test(adjudicator: Adjudicator, records: list[dict], preds: list[dict], k: int, workers: int) -> dict:
    subset = list(zip(records, preds))[:k]

    def run(pair: tuple[dict, dict]) -> dict:
        rec, original = pair

        seed = int(rec["application_id"].split("-")[-1])
        narrative, identity = counterfactual_narrative(rec, seed=seed)
        swapped = adjudicator.run(narrative, rec["application_id"])
        return {
            "application_id": rec["application_id"],
            "from": {a: rec["identity"][a] for a in FAIRNESS_ATTRS},
            "to": {a: identity[a] for a in FAIRNESS_ATTRS},
            "decision_flipped": swapped["decision"] != original["decision"],
            "extraction_changed": swapped["extracted_application"] != original["extracted_application"],
            "original_decision": original["decision"],
            "swapped_decision": swapped["decision"],
        }

    with ThreadPoolExecutor(max_workers=workers) as pool:
        rows = list(pool.map(run, subset))
    return {
        "n": len(rows),
        "decision_flip_rate": round(sum(r["decision_flipped"] for r in rows) / max(len(rows), 1), 4),
        "extraction_change_rate": round(sum(r["extraction_changed"] for r in rows) / max(len(rows), 1), 4),
        "flips": [r for r in rows if r["decision_flipped"]],
    }

def baseline_metrics(models_dir: Path, records: list[dict]) -> dict:
    """Score every text-input baseline saved by train.py on the same records."""
    import joblib

    texts = [r.get("narrative_masked", r["narrative"]) for r in records]
    y_true = [r["label"] for r in records]
    out = {}
    for name in BASELINES:
        if (path := models_dir / f"{name}.joblib").exists():
            out[name] = decision_metrics(y_true, joblib.load(path).predict(texts).tolist())
    return out

def pick_samples(records: list[dict], preds: list[dict], n: int) -> list[int]:
    chosen: list[int] = []
    for label in LABELS:
        for i, rec in enumerate(records):
            if rec["label"] == label and i not in chosen:
                chosen.append(i)
                break
    for i, rec in enumerate(records):
        if len(chosen) >= n:
            break
        if i not in chosen and (rec["scenario"] in {"edge", "reject_and_review"} or preds[i]["decision"] != rec["label"]):
            chosen.append(i)
    return chosen[:n]

def write_samples(path: Path, records: list[dict], preds: list[dict], idx: list[int]) -> None:
    lines = ["# Sample adjudications (validation set)", ""]
    for i in idx:
        rec, pred = records[i], preds[i]
        output = {k: pred[k] for k in ("decision", "failed_rules", "missing_information", "reasoning")}
        lines += [
            f"## {rec['application_id']} - scenario `{rec['scenario']}` - truth `{rec['label']}` - predicted `{pred['decision']}`",
            "",
            f"> {rec['narrative']}",
            "",
            "```json",
            json.dumps(output, indent=2),
            "```",
            "",
        ]
    path.write_text("\n".join(lines))

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default=str(PROJECT_ROOT / "data" / "processed" / "val.jsonl"))
    parser.add_argument("--extractor", choices=["auto", "llm", "regex"], default="auto")
    parser.add_argument("--explainer", choices=["auto", "llm", "template"], default="auto")
    parser.add_argument("--limit", type=int, default=0, help="Evaluate only the first N records (0 = all)")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--counterfactual", type=int, default=100, help="Records to re-run with swapped identity")
    parser.add_argument("--samples", type=int, default=8)
    parser.add_argument("--models-dir", default=str(PROJECT_ROOT / "models"))
    parser.add_argument("--out", default=str(PROJECT_ROOT / "reports"))
    args = parser.parse_args()

    records = load(Path(args.data))
    if args.limit:
        records = records[: args.limit]
    adjudicator = build_adjudicator(args.extractor, args.explainer)
    for rec in records:
        if "label" not in rec:
            truth = adjudicator.engine.evaluate(rec["truth"])
            rec["label"] = truth.decision
            rec["failed_rule_ids"] = [r.rule.id for r in truth.failed]
            rec["missing_rule_ids"] = [r.rule.id for r in truth.missing]
    mode = f"{type(adjudicator.extractor).__name__} + {type(adjudicator.explainer).__name__}"
    print(f"Evaluating {len(records)} records with {mode} ...")

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        preds = list(pool.map(lambda r: adjudicator.run(r["narrative"], r["application_id"]), records))

    y_true, y_pred = [r["label"] for r in records], [p["decision"] for p in preds]
    rule_match = [set(r["failed_rule_ids"] + r["missing_rule_ids"]) ==
                  {x["id"] for x in p["failed_rules"] + p["missing_information"]} for r, p in zip(records, preds)]

    metrics = {
        "mode": mode,
        "n": len(records),
        "decision": decision_metrics(y_true, y_pred),
        "rule_set_exact_match": round(sum(rule_match) / len(rule_match), 4),
        "decision_accuracy_by_scenario": {
            s: round(sum(r["label"] == p["decision"] for r, p in zip(records, preds) if r["scenario"] == s)
                     / sum(r["scenario"] == s for r in records), 4)
            for s in sorted({r["scenario"] for r in records})
        },
        "extraction": extraction_metrics(records, preds),
        "explanation": explanation_metrics(preds),
    }

    has_identity = all("identity" in r for r in records)
    if has_identity:
        metrics["fairness"] = fairness_metrics(records, preds)
    if args.counterfactual and has_identity:
        metrics["counterfactual"] = counterfactual_test(adjudicator, records, preds, args.counterfactual, args.workers)
    if baselines := baseline_metrics(Path(args.models_dir), records):
        metrics["baselines"] = baselines

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2))
    with (out / "predictions.jsonl").open("w") as f:
        for pred in preds:
            f.write(json.dumps(pred) + "\n")
    write_samples(out / "sample_outputs.md", records, preds, pick_samples(records, preds, args.samples))

    d = metrics["decision"]
    print(f"\nDecision   accuracy={d['accuracy']} (95% CI {d['accuracy_95ci']})  macro_f1={d['macro_f1']}"
          f"  reject_recall={d['reject_recall']}  false_approvals={d['false_approvals']}")
    print(f"Rules      exact rule-set match={metrics['rule_set_exact_match']}")
    print(f"Extraction all-fields exact={metrics['extraction']['all_fields_exact']}")
    for field, acc in metrics["extraction"]["per_field_accuracy"].items():
        print(f"           {field:<48} {acc}")
    print(f"Explain    sources={dict(metrics['explanation']['sources'])}"
          f"  guardrail_issues={dict(metrics['explanation']['guardrail_issue_counts'])}")
    for attr, fm in metrics.get("fairness", {}).items():
        print(f"Fairness   {attr:<10} pred_DI={fm['pred_disparate_impact']}  truth_DI={fm['truth_disparate_impact']}"
              f"  error_gap={fm['error_rate_gap']}  4/5ths={'PASS' if fm['four_fifths_rule_pass'] else 'FAIL'}")
    if "counterfactual" in metrics:
        cf = metrics["counterfactual"]
        print(f"Counterfactual n={cf['n']} decision_flip_rate={cf['decision_flip_rate']}"
              f" extraction_change_rate={cf['extraction_change_rate']}")
    for name, b in metrics.get("baselines", {}).items():
        print(f"Baseline   {name:<16} accuracy={b['accuracy']} (95% CI {b['accuracy_95ci']}) macro_f1={b['macro_f1']}"
              f" false_approvals={b['false_approvals']}")
    print(f"\nWrote {out / 'metrics.json'}, {out / 'predictions.jsonl'}, {out / 'sample_outputs.md'}")

if __name__ == "__main__":
    main()
