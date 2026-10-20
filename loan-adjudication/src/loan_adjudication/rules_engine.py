"""Deterministic evaluator for the JSON credit-rule policy. This is the sole decision maker."""

from __future__ import annotations

import json
import operator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .schema import get_field

ACTION_PRIORITY = {"APPROVE": 0, "FLAG_REVIEW": 1, "REJECT": 2}
SEVERITY_RANK = {"CRITICAL": 0, "MAJOR": 1, "MINOR": 2}
EMPLOYED_STATUSES = frozenset({"employed_full_time", "employed_part_time", "self_employed"})

_OPERATORS: dict[str, Callable[[Any, Any], bool]] = {
    ">=": operator.ge,
    "<=": operator.le,
    ">": operator.gt,
    "<": operator.lt,
    "==": operator.eq,
    "is": lambda a, b: a is b,
    "in": lambda a, b: a in b,
    "not_in": lambda a, b: a not in b,
}

# Tenure is only meaningful for applicants who currently hold a job (retirees have no "current role").
_APPLICABILITY: dict[str, Callable[[dict], bool]] = {
    "RULE-EMPLOY-002": lambda app: get_field(app, "applicant.employment_status") in EMPLOYED_STATUSES | {None},
}

@dataclass(frozen=True)
class Rule:
    id: str
    name: str
    description: str
    field: str
    operator: str
    action_on_fail: str
    severity: str
    group: str
    value: Any = None
    value_field_multiplier: str | None = None
    multiplier_value: float | None = None
    unit: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "Rule":
        if data["operator"] not in _OPERATORS:
            raise ValueError(f"Unsupported operator {data['operator']!r} in rule {data['id']}")
        if data["action_on_fail"] not in ACTION_PRIORITY:
            raise ValueError(f"Unsupported action {data['action_on_fail']!r} in rule {data['id']}")
        kwargs = {k: data[k] for k in cls.__dataclass_fields__ if k in data}
        if isinstance(kwargs.get("value"), list):
            kwargs["value"] = tuple(kwargs["value"])
        return cls(**kwargs)

    def threshold(self, application: dict) -> Any:
        if self.value_field_multiplier:
            base = get_field(application, self.value_field_multiplier)
            return None if base is None else base * self.multiplier_value
        return self.value

    def as_prompt_line(self) -> str:
        if self.value_field_multiplier:
            requirement = f"{self.field} {self.operator} {self.multiplier_value} x {self.value_field_multiplier}"
        else:
            value = list(self.value) if isinstance(self.value, tuple) else self.value
            requirement = f"{self.field} {self.operator} {json.dumps(value)}"
        return (
            f"- {self.id} | {self.name} | severity={self.severity} | on_fail={self.action_on_fail}\n"
            f"  requirement: {requirement}\n  meaning: {self.description}"
        )

@dataclass
class RuleResult:
    rule: Rule
    status: str  # PASS | FAIL | MISSING | NOT_APPLICABLE
    observed: Any
    required: Any

    def to_dict(self) -> dict:
        required = list(self.required) if isinstance(self.required, tuple) else self.required
        return {
            "id": self.rule.id,
            "name": self.rule.name,
            "status": self.status,
            "action_on_fail": self.rule.action_on_fail,
            "severity": self.rule.severity,
            "field": self.rule.field,
            "observed": self.observed,
            "required": required,
        }

def _issue_sort_key(result: RuleResult) -> tuple[int, int]:
    return (-ACTION_PRIORITY[result.rule.action_on_fail], SEVERITY_RANK.get(result.rule.severity, 9))

@dataclass
class Adjudication:
    decision: str
    results: list[RuleResult]
    policy_version: str

    @property
    def failed(self) -> list[RuleResult]:
        return sorted((r for r in self.results if r.status == "FAIL"), key=_issue_sort_key)

    @property
    def missing(self) -> list[RuleResult]:
        return sorted((r for r in self.results if r.status == "MISSING"), key=_issue_sort_key)

    @property
    def issue_ids(self) -> list[str]:
        return [r.rule.id for r in self.failed + self.missing]

    def to_dict(self) -> dict:
        return {
            "decision": self.decision,
            "policy_version": self.policy_version,
            "results": [r.to_dict() for r in self.results],
        }

@dataclass
class RulesEngine:
    rules: list[Rule]
    version: str = "unknown"
    description: str = ""
    _by_id: dict[str, Rule] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._by_id = {r.id: r for r in self.rules}

    @classmethod
    def from_file(cls, path: str | Path) -> "RulesEngine":
        data = json.loads(Path(path).read_text())
        policy = data["personal_loan_credit_rules"]
        return cls(
            rules=[Rule.from_dict(r) for r in policy["rules"]],
            version=policy.get("version", "unknown"),
            description=policy.get("description", ""),
        )

    def rule(self, rule_id: str) -> Rule:
        return self._by_id[rule_id]

    def evaluate(self, application: dict) -> Adjudication:
        results: list[RuleResult] = []
        for rule in self.rules:
            observed = get_field(application, rule.field)
            required = rule.threshold(application)
            if not _APPLICABILITY.get(rule.id, lambda _: True)(application):
                status = "NOT_APPLICABLE"
            elif observed is None or required is None:
                status = "MISSING"
            else:
                try:
                    status = "PASS" if _OPERATORS[rule.operator](observed, required) else "FAIL"
                except TypeError:
                    status = "MISSING"
            results.append(RuleResult(rule, status, observed, required))

        # Precedence: any REJECT failure > any FLAG_REVIEW failure or unverifiable field > APPROVE.
        decision = "APPROVE"
        for result in results:
            if result.status == "FAIL":
                action = result.rule.action_on_fail
            elif result.status == "MISSING":
                action = "FLAG_REVIEW"
            else:
                continue
            if ACTION_PRIORITY[action] > ACTION_PRIORITY[decision]:
                decision = action
        return Adjudication(decision=decision, results=results, policy_version=self.version)

    def render_for_prompt(self) -> str:
        lines = [f"Personal loan credit policy v{self.version}: {self.description}", ""]
        lines += [r.as_prompt_line() for r in self.rules]
        lines += [
            "",
            "Decision precedence: any failed REJECT rule -> REJECT; otherwise any failed FLAG_REVIEW rule "
            "or any rule whose input could not be verified -> FLAG_REVIEW; otherwise APPROVE.",
            "RULE-EMPLOY-002 only applies to applicants who are currently employed or self-employed.",
        ]
        return "\n".join(lines)
