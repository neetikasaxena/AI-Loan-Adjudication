"""Inputs for the learned baselines: digit-masked text and numeric features from extracted facts."""

from __future__ import annotations

import re

import numpy as np

from .extractor import RegexExtractor
from .schema import EMPLOYMENT_STATUSES, RESIDENCY_STATUSES, to_application

NUMERIC_FIELDS = (
    "age",
    "credit_score",
    "annual_income_usd",
    "debt_to_income_ratio_percent",
    "current_employment_duration_months",
)
_NUMBER = re.compile(r"\d+(?:[.,]\d+)*")

def mask_digits(text: str) -> str:
    """Numbers become one token so a bag-of-words model cannot memorise specific values."""
    return _NUMBER.sub(" <num> ", text.lower())

def _value(v) -> tuple[float, float]:
    return (-1.0, 1.0) if v is None else (float(v), 0.0)

def featurize(application: dict) -> list[float]:
    """Fixed-length vector: each value plus an is-missing flag (missing values encoded as -1)."""
    a = application["applicant"]
    loan = application["loan_application"]["requested_amount_usd"]
    income = a.get("annual_income_usd")
    row: list[float] = []
    for name in NUMERIC_FIELDS:
        row += _value(a.get(name))
    row += _value(loan / income if loan is not None and income else None)
    row += [float(a.get("employment_status") == s) for s in EMPLOYMENT_STATUSES]
    row.append(float(a.get("employment_status") is None))
    row += [float(a.get("residency_status") == s) for s in RESIDENCY_STATUSES]
    row.append(float(a.get("residency_status") is None))
    for name in ("has_bankruptcy_recent", "has_verifiable_bank_account"):
        v = a.get(name)
        row += [float(v is True), float(v is None)]
    return row

FEATURE_NAMES = (
    [n for f in NUMERIC_FIELDS for n in (f, f"{f}_missing")]
    + ["loan_to_income", "loan_to_income_missing"]
    + [f"employment={s}" for s in EMPLOYMENT_STATUSES] + ["employment_missing"]
    + [f"residency={s}" for s in RESIDENCY_STATUSES] + ["residency_missing"]
    + ["bankruptcy_recent", "bankruptcy_missing", "bank_account", "bank_account_missing"]
)

def texts_to_features(texts) -> np.ndarray:
    extractor = RegexExtractor()
    return np.array([featurize(to_application(extractor.extract(t).raw)) for t in texts])

def applications_to_features(applications) -> np.ndarray:
    return np.array([featurize(a) for a in applications])
