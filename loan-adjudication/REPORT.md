# AI Loan Adjudication: Approach, Results and Analysis

**Summary.** A rules engine over the client's `credit_rules.json` makes every decision. An LLM (regex
fallback) turns free text into facts, and an LLM (template fallback) writes the explanation, checked by a
guardrail. On phrasing never seen in training, end-to-end text classifiers reach 45–48% with 20–30 wrongful
approvals; the rules pipeline with a simple regex extractor reaches 46% with **zero**. With correct facts a
learned tree reaches 98.5%, so **fact extraction is the bottleneck**. The LLM extractor is the next thing to
measure, once endpoint access is available.

## 1. Approach

The dataset is a **policy** (10 rules), not labelled applications. Training data is therefore synthesised
and labelled by applying the rules. Because the rules are fixed thresholds, the decision itself is a lookup,
not a learning problem, so each part of the task goes to the component suited to it:

| Step | Component | Why |
| --- | --- | --- |
| Text → facts | LLM (regex fallback) | Free text varies; needs unit conversion and disambiguation |
| Facts → decision | Rules engine over `credit_rules.json` | Exact, auditable; a policy change is a JSON edit |
| Decision → explanation | LLM with the rules as system prompt + guardrail (template fallback) | Clear letters without decision authority |

- **Rules as LLM instructions:** yes, for the explanation only. The LLM sees rule outcomes, not the
  narrative or identity, and must repeat the engine's decision and rule IDs or its letter is discarded.
- **Fine-tuning:** not required; prompting suffices. Fine-tuning-ready data is produced in case a small
  self-hosted model is later needed.
- **"Dialogues":** the brief's term is ambiguous, so both single-turn applications and multi-turn intake
  chats are supported.

**Flow:** (1) read rules → (2) generate 2,000 applicants → (3) label with rules → (4) 80/20 split →
(5) write as narrative + dialogue → (6) tokenize → (7) train baselines → inference: (8) extract facts →
(9) apply rules → (10) explain.

## 2. Data preparation

- **Generation and labels.** 2,000 applicants across approve / reject / review / mixed / threshold-edge
  scenarios (edge cases at 669/670/671, DTI 39.9/40/40.1, etc.). Labels come from the rules engine:
  39% APPROVE, 19% FLAG_REVIEW, 42% REJECT.
- **Text.** Each applicant is written as a free-text narrative and as an intake dialogue (mean 16 turns, with
  follow-ups when a fact is withheld). Text varies number formats, monthly vs annual income, DTI vs debt
  amounts, and includes distractors (rent, an old credit score); ~6% of facts are omitted to test the
  "missing → review" path.
- **Split.** 80/20 stratified by label (1,600 / 400). **Validation uses wordings never seen in training**,
  so it measures generalisation rather than memorisation.
- **Fairness controls.** Gender, ethnicity and region are sampled independently of finances. Training text
  is identity-masked (`[NAME]`, `[CITY]`, neutral pronouns).
- **Tokenization.** Chat format; role markers `<|system|>`, `<|user|>`, `<|assistant|>` are added as special
  tokens when the tokenizer has no chat template; loss is masked (`-100`) on everything except assistant
  turns; sequences are right-padded to 704 with **no truncation**, since cutting would lose instructions or
  answers. A compact system prompt (44 tokens instead of the 808-token policy) keeps examples short.
  Hugging Face is blocked on the build network, so the cached `roberta-large` tokenizer was used.
- **Limitations.** Income is not correlated with age or job, no applicant fails more than two rules, and
  there are only 3 phrasings per fact.

## 3. Results

Run offline (regex extractor + template explainer); LLM rows need the internal endpoint.

**Validation (n = 400, unseen wordings)**

| Model | Train | Validation (95% CI) | Macro-F1 | Wrongful approvals |
| --- | --- | --- | --- | --- |
| TF-IDF + logistic regression (original) | 0.994 | 0.483 (0.43–0.53) | 0.368 | 20 |
| TF-IDF + LR, regularised by 5-fold CV | 0.731 | 0.450 (0.40–0.50) | 0.352 | 30 |
| Regex facts → decision tree | 1.000 | 0.328 (0.28–0.37) | 0.271 | 0 |
| True facts → decision tree (ceiling) | 1.000 | **0.985** | 0.982 | 0 |
| **Regex extractor + rules engine** | 1.000 | 0.463 (0.42–0.51) | 0.401 | **0** |
| LLM extractor + rules engine | *pending endpoint* | | | |

Dialogues give the same picture (rules pipeline 46%, 0 wrongful approvals). On the 10 hand-written
applications all models score 30–60%, with confidence intervals too wide (±30 points) to rank them.

**Key findings**
1. **Memorised wording inflated earlier scores.** With shared phrasing the TF-IDF model scored 66% and the
   rules pipeline 100%; unseen phrasing exposed both.
2. **Regularisation narrows the train–validation gap (51 → 28 points) but not the error.** A bag of words
   cannot represent "credit score ≥ 670".
3. **With correct facts, a learned model rediscovers the policy.** The tree splits at the client's thresholds
   (loan/income 0.50, credit 670, tenure 6 months) and reaches 98.5%.
4. **Extraction is the bottleneck.** On unseen wording the regex reads age, credit score and residency
   perfectly but misses income, loan amount and DTI, so it routes every case to review rather than guess.
5. **Fairness.** Swapping gender, ethnicity and region on 100 applications changed no decisions. Group
   approval-rate gaps exist in the ground truth itself (sampling noise; identity is independent of finances).

## 4. Strengths and weaknesses

**Strengths**
- Decisions are only as wrong as the extracted facts, and every reason cites a rule, the applicant's value
  and the requirement.
- Fails safe: unknown facts go to manual review, never approval (0 wrongful approvals vs 20–30 for classifiers).
- Policy changes are a JSON edit; decisions, labels, explanation wording and prompts follow automatically.
- Identity never reaches the decision or the explainer.

**Weaknesses**
- **Extraction quality** is unproven until the LLM extractor is measured on varied, real text.
- **Synthetic data** is template-bound and somewhat unrealistic (see section 2).
- **The rules file does not yet drive generation:** thresholds, tips and the 7-year bankruptcy window are
  hard-coded copies, so a policy change would not update generated edge cases.
- **Policy ambiguities** were resolved by assumption (inclusive thresholds, tenure rule skipped for retirees,
  "within 7 years" as ≤ 7) and need confirmation.
- **Explanations** are checked for faithfulness, not tone; adverse-action wording needs compliance review.
- **Self-reported facts:** production would verify income and accounts against bureau and bank data.

## 5. Next steps
1. Run the LLM extractor and explainer on the internal endpoint; compare with the 98.5% ceiling.
2. Drive data generation and tips from `credit_rules.json`, with a test that a threshold change propagates.
3. Add LLM paraphrases, realistic correlations, applications failing 3+ rules, and a 100–200-case
   hand-written holdout including prompt-injection attempts.
4. Route low-confidence or conflicting extractions to review.
5. Fine-tune a small model with LoRA on the prepared data once approved base-model weights are available.
