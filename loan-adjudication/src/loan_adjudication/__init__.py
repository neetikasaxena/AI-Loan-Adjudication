"""Hybrid personal-loan adjudication: deterministic rules engine + LLM extraction/explanation."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RULES_PATH = PROJECT_ROOT / "data" / "credit_rules.json"
