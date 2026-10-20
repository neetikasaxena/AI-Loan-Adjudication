"""Applicant-facing explanations. The LLM only writes the reasoning; decision and rule list come from the engine."""

from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass, field

from .llm_client import LLMClient, LLMError
from .rules_engine import Adjudication, RuleResult, RulesEngine

FIELD_LABELS = {
    "applicant.age": "age",
    "applicant.credit_score": "credit score",
    "applicant.annual_income_usd": "annual income",
    "applicant.debt_to_income_ratio_percent": "debt-to-income ratio",
    "applicant.employment_status": "employment status",
    "applicant.current_employment_duration_months": "time in your current role",
    "applicant.residency_status": "residency status",
    "applicant.has_bankruptcy_recent": "bankruptcy history",
    "applicant.has_verifiable_bank_account": "bank account",
    "loan_application.requested_amount_usd": "requested loan amount",
}
ENUM_LABELS = {
    "employed_full_time": "employed full-time",
    "employed_part_time": "employed part-time",
    "self_employed": "self-employed",
    "retired": "retired",
    "unemployed": "unemployed",
    "student": "a student",
    "US_Citizen": "U.S. citizen",
    "Permanent_Resident": "permanent resident",
    "Visa_Holder": "visa holder",
    "Non_Resident": "non-resident",
}
TIPS = {
    "RULE-AGE-001": "You are welcome to reapply once you turn 18.",
    "RULE-CREDIT-001": "Paying down balances and making on-time payments can raise your score; you may reapply once it reaches 670.",
    "RULE-INCOME-001": "You may reapply once your verified income reaches $30,000 or if you can document additional income.",
    "RULE-DTI-001": "Lowering your monthly debt payments would bring your ratio down.",
    "RULE-EMPLOY-001": "You may reapply once you have a steady source of income such as employment or retirement income.",
    "RULE-EMPLOY-002": "An underwriter may ask for recent pay stubs or prior employment history to confirm income stability.",
    "RULE-RESIDENCY-001": "This product is currently available only to U.S. citizens and permanent residents.",
    "RULE-BANKRUPTCY-001": "You may become eligible once the filing is more than 7 years old.",
    "RULE-LOANAMT-001": "An underwriter will check affordability; a smaller amount (up to half your annual income) can be decided automatically.",
    "RULE-BANKACCTS-001": "Opening a checking or savings account would satisfy this requirement.",
}
# Terms an applicant-facing explanation must never contain (protected characteristics / proxies).
PROTECTED_TERMS = re.compile(
    r"\b(gender|male|female|\bhe\b|\bshe\b|race|racial|ethnic\w*|religio\w*|marital|married|pregnan\w*|"
    r"national origin|neighbou?rhood|zip code|hispanic|latino|asian|black|white)\b",
    re.IGNORECASE,
)

def fmt_value(path: str, value) -> str:
    if value is None:
        return "not provided"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (list, tuple)):
        return ", ".join(fmt_value(path, v) for v in value)
    if isinstance(value, str):
        return ENUM_LABELS.get(value, value.replace("_", " "))
    if path.endswith("_usd"):
        return f"${value:,.0f}"
    if path.endswith("_percent"):
        return f"{round(value, 2):g}%"
    if path.endswith("_months"):
        return f"{int(value)} months"
    return f"{value:g}"

def requirement_text(result: RuleResult) -> str:
    rule = result.rule
    if rule.operator == ">=":
        text = f"at least {fmt_value(rule.field, result.required)}"
    elif rule.operator == "<=":
        text = f"no more than {fmt_value(rule.field, result.required)}"
    elif rule.operator == "in":
        text = f"one of: {fmt_value(rule.field, rule.value)}"
    else:
        return rule.description
    if rule.value_field_multiplier:
        text += f" ({rule.multiplier_value:.0%} of your {FIELD_LABELS.get(rule.value_field_multiplier, 'income')})"
    return text

def issue_dict(result: RuleResult) -> dict:
    return {
        "id": result.rule.id,
        "name": result.rule.name,
        "status": result.status,
        "action_on_fail": result.rule.action_on_fail,
        "severity": result.rule.severity,
        "your_value": fmt_value(result.rule.field, result.observed),
        "requirement": requirement_text(result),
    }

def _pick(options: list[str], rng: random.Random | None) -> str:
    return options[0] if rng is None else rng.choice(options)


# First option of each list is the default wording; the rest are used for varied training targets.
APPROVE_OPENERS = [
    "Good news: your application meets every requirement of our personal loan policy.",
    "We're pleased to let you know that your application meets all of our lending criteria.",
    "Your application has been approved because it satisfies every requirement of our personal loan policy.",
]
APPROVE_FACTS = ["Key factors were your {facts}.", "In particular, we looked at your {facts}."]
REJECT_OPENERS = [
    "We are unable to approve your application at this time.",
    "Unfortunately, we can't approve your application right now.",
    "After reviewing your application, we are not able to approve it at this time.",
]
REVIEW_OPENERS = [
    "Your application needs a manual review by an underwriter before a final decision can be made.",
    "Before we can make a final decision, an underwriter needs to review your application.",
    "Your application has been referred to an underwriter for a closer look.",
]
FAIL_FORMS = [
    "Your {label} is {observed}, but the requirement is {requirement}.",
    "The policy requires your {label} to be {requirement}; yours is {observed}.",
    "Your {label} of {observed} does not meet the requirement of {requirement}.",
]
MISSING_FORMS = [
    "We could not confirm your {label} from the information provided; please submit documentation of it.",
    "Your {label} was not provided, so we will need documentation of it to continue.",
]
ALSO_REVIEW_FORMS = ["Separately, these items would also need review: {items}.",
                     "Other items that would also need attention: {items}."]


def _issue_sentence(result: RuleResult, rng: random.Random | None = None) -> str:
    rule_id, label = result.rule.id, FIELD_LABELS.get(result.rule.field, result.rule.field)
    if result.status == "MISSING":
        return _pick(MISSING_FORMS, rng).format(label=label)
    if rule_id == "RULE-BANKRUPTCY-001":
        return "Your application shows a bankruptcy filing within the last 7 years, and the policy requires none in that period."
    if rule_id == "RULE-BANKACCTS-001":
        return "We could not confirm an active bank account, which is needed to send the funds and collect repayments."
    observed = fmt_value(result.rule.field, result.observed)
    return _pick(FAIL_FORMS, rng).format(label=label, observed=observed, requirement=requirement_text(result))

@dataclass
class Explanation:
    decision: str
    failed_rules: list[dict]
    missing_information: list[dict]
    reasoning: str
    source: str
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "decision": self.decision,
            "failed_rules": self.failed_rules,
            "missing_information": self.missing_information,
            "reasoning": self.reasoning,
            "explanation_source": self.source,
            "guardrail_issues": self.issues,
        }

class TemplateExplainer:
    def reasoning(self, adj: Adjudication, variant: int | None = None) -> str:
        """variant=None gives the canonical wording; an int seeds a reproducible paraphrase."""
        rng = None if variant is None else random.Random(variant)
        if adj.decision == "APPROVE":
            passed = {r.rule.id: r for r in adj.results if r.status == "PASS"}
            facts = []
            for rule_id in ("RULE-CREDIT-001", "RULE-DTI-001", "RULE-INCOME-001"):
                if r := passed.get(rule_id):
                    facts.append(f"{FIELD_LABELS[r.rule.field]} of {fmt_value(r.rule.field, r.observed)} ({requirement_text(r)} required)")
            opener = _pick(APPROVE_OPENERS, rng)
            return f"{opener} {_pick(APPROVE_FACTS, rng).format(facts='; '.join(facts))}" if facts else opener

        blocking = [r for r in adj.failed if r.rule.action_on_fail == "REJECT"]
        review = [r for r in adj.failed if r.rule.action_on_fail == "FLAG_REVIEW"] + adj.missing
        parts: list[str] = []
        if adj.decision == "REJECT":
            parts.append(_pick(REJECT_OPENERS, rng))
            parts += [_issue_sentence(r, rng) for r in blocking]
            parts += [TIPS[r.rule.id] for r in blocking if r.rule.id in TIPS]
            if review:
                parts.append(_pick(ALSO_REVIEW_FORMS, rng).format(items="; ".join(r.rule.name for r in review)))
        else:
            parts.append(_pick(REVIEW_OPENERS, rng))
            parts += [_issue_sentence(r, rng) for r in review]
            parts += [TIPS[r.rule.id] for r in adj.failed if r.rule.id in TIPS]
        return " ".join(parts)

    def explain(self, adj: Adjudication, variant: int | None = None) -> Explanation:
        return Explanation(
            decision=adj.decision,
            failed_rules=[issue_dict(r) for r in adj.failed],
            missing_information=[issue_dict(r) for r in adj.missing],
            reasoning=self.reasoning(adj, variant),
            source="template",
        )

EXPLAINER_GUIDELINES = """\
You write decision letters for personal-loan applicants. The decision has ALREADY been made by a deterministic
rules engine applying the policy below. You must NOT change the decision, add or drop rules, or invent facts.

{policy}

Writing guidelines:
- Address the applicant directly as "you", in plain, respectful language, 60-150 words.
- For each failed or unverifiable rule, state the applicant's value and the requirement.
- REJECT: name the requirements not met and what could change the outcome in future.
- FLAG_REVIEW: explain that an underwriter will review the application, why, and what documents would help.
- APPROVE: briefly confirm the key criteria that were met.
- Never mention or speculate about gender, race, ethnicity, religion, marital status, national origin or
  neighbourhood. Do not mention interest rates, fees or terms that were not provided.

Return ONLY JSON: {{"decision": "<same decision>", "failed_rules": ["<rule ids from the input, failed and unverifiable>"], "reasoning": "<letter text>"}}"""

class LLMExplainer:
    def __init__(self, client: LLMClient, engine: RulesEngine, fallback: TemplateExplainer | None = None):
        self.client = client
        self.system_prompt = EXPLAINER_GUIDELINES.format(policy=engine.render_for_prompt())
        self.fallback = fallback or TemplateExplainer()

    def explain(self, adj: Adjudication) -> Explanation:
        base = self.fallback.explain(adj)
        # Data minimisation: the LLM sees rule outcomes only, never the narrative, name or location.
        payload = {
            "decision": adj.decision,
            "failed_rules": base.failed_rules,
            "unverifiable_rules": base.missing_information,
            "rules_passed": [r.rule.id for r in adj.results if r.status == "PASS"],
        }
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": json.dumps(payload, indent=2)},
        ]
        try:
            out = self.client.chat_json(messages, temperature=0.2, max_tokens=600)
        except LLMError as exc:
            base.source, base.issues = "template_fallback", [f"llm_error: {exc}"]
            return base

        issues = validate_explanation(out, adj)
        if issues:
            base.source, base.issues = "template_fallback", issues
            return base
        base.reasoning, base.source = out["reasoning"].strip(), "llm"
        return base

def validate_explanation(out: dict, adj: Adjudication) -> list[str]:
    """Guardrail: the LLM letter must agree with the engine and stay clear of protected attributes."""
    issues = []
    if out.get("decision") != adj.decision:
        issues.append(f"decision_mismatch: {out.get('decision')!r} != {adj.decision!r}")
    claimed = out.get("failed_rules") or []
    if not isinstance(claimed, list) or set(map(str, claimed)) != set(adj.issue_ids):
        issues.append(f"rule_mismatch: {claimed!r} != {adj.issue_ids!r}")
    reasoning = out.get("reasoning")
    if not isinstance(reasoning, str) or len(reasoning.split()) < 10:
        issues.append("reasoning_missing_or_too_short")
    elif m := PROTECTED_TERMS.search(reasoning):
        issues.append(f"protected_term: {m.group(0)!r}")
    return issues
