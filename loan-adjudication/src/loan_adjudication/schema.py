"""Canonical applicant schema shared by the data generator, extractors and rules engine."""

from __future__ import annotations

from typing import Any

EMPLOYMENT_STATUSES = (
    "employed_full_time",
    "employed_part_time",
    "self_employed",
    "retired",
    "unemployed",
    "student",
)
RESIDENCY_STATUSES = ("US_Citizen", "Permanent_Resident", "Visa_Holder", "Non_Resident")
BANKRUPTCY_LOOKBACK_YEARS = 7

# Raw facts an extractor pulls from a narrative; derived policy fields are computed in to_application().
RAW_FIELDS: dict[str, str] = {
    "age": "integer, applicant age in years",
    "credit_score": "integer FICO score (300-850); if several are mentioned use the CURRENT one",
    "annual_income_usd": "number, gross annual income (only if stated per year)",
    "monthly_income_usd": "number, gross monthly income (only if stated per month)",
    "debt_to_income_ratio_percent": "number, debt-to-income ratio in percent (only if stated explicitly)",
    "monthly_debt_payments_usd": "number, total monthly debt payments excluding rent/mortgage (only if stated)",
    "employment_status": f"one of {list(EMPLOYMENT_STATUSES)}",
    "current_employment_duration_months": "integer, months in current job/business (convert years to months)",
    "residency_status": f"one of {list(RESIDENCY_STATUSES)} (green card = Permanent_Resident)",
    "bankruptcy_filed": "boolean, true if the applicant has EVER filed for bankruptcy, false if they say they never have",
    "bankruptcy_years_ago": "number, how many years ago the most recent bankruptcy was filed",
    "has_verifiable_bank_account": "boolean, true if the applicant has an active bank account",
    "requested_amount_usd": "number, personal loan amount requested",
}

APPLICANT_FIELDS = (
    "age",
    "credit_score",
    "annual_income_usd",
    "debt_to_income_ratio_percent",
    "employment_status",
    "current_employment_duration_months",
    "residency_status",
    "has_bankruptcy_recent",
    "has_verifiable_bank_account",
)

def get_field(application: dict, path: str) -> Any:
    node: Any = application
    for part in path.split("."):
        if not isinstance(node, dict):
            return None
        node = node.get(part)
    return node

def iter_fields(application: dict):
    for name in APPLICANT_FIELDS:
        yield f"applicant.{name}", application.get("applicant", {}).get(name)
    yield "loan_application.requested_amount_usd", application.get("loan_application", {}).get("requested_amount_usd")

def compute_dti(monthly_debt_usd: float, annual_income_usd: float) -> float | None:
    if not annual_income_usd:
        return None
    return round(monthly_debt_usd / (annual_income_usd / 12) * 100, 2)

def _num(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace(",", "").replace("$", "").replace("%", "").strip())
    except ValueError:
        return None

def _int(value: Any) -> int | None:
    number = _num(value)
    return None if number is None else int(round(number))

def _bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "y"}:
            return True
        if lowered in {"false", "no", "n"}:
            return False
    return None

def _enum(value: Any, allowed: tuple[str, ...]) -> str | None:
    if not isinstance(value, str):
        return None
    lookup = {item.lower(): item for item in allowed}
    return lookup.get(value.strip().lower())

def to_application(raw: dict) -> dict:
    """Normalise extractor output into the nested structure the rules reference (unknown -> None)."""
    income = _num(raw.get("annual_income_usd"))
    monthly_income = _num(raw.get("monthly_income_usd"))
    if income is None and monthly_income is not None:
        income = monthly_income * 12

    dti = _num(raw.get("debt_to_income_ratio_percent"))
    monthly_debt = _num(raw.get("monthly_debt_payments_usd"))
    if dti is None and monthly_debt is not None and income:
        dti = compute_dti(monthly_debt, income)

    filed = _bool(raw.get("bankruptcy_filed"))
    years_ago = _num(raw.get("bankruptcy_years_ago"))
    if filed is False:
        recent = False
    elif years_ago is not None:
        recent = years_ago <= BANKRUPTCY_LOOKBACK_YEARS
    else:
        # Filed but timing unknown, or never mentioned: cannot verify.
        recent = None

    return {
        "applicant": {
            "age": _int(raw.get("age")),
            "credit_score": _int(raw.get("credit_score")),
            "annual_income_usd": income,
            "debt_to_income_ratio_percent": dti,
            "employment_status": _enum(raw.get("employment_status"), EMPLOYMENT_STATUSES),
            "current_employment_duration_months": _int(raw.get("current_employment_duration_months")),
            "residency_status": _enum(raw.get("residency_status"), RESIDENCY_STATUSES),
            "has_bankruptcy_recent": recent,
            "has_verifiable_bank_account": _bool(raw.get("has_verifiable_bank_account")),
        },
        "loan_application": {"requested_amount_usd": _num(raw.get("requested_amount_usd"))},
    }
