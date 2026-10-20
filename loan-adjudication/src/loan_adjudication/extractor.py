"""Narrative -> raw facts. LLM extractor (primary) and a regex extractor (offline baseline / fallback)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .llm_client import LLMClient, LLMError
from .schema import RAW_FIELDS

@dataclass
class ExtractionResult:
    raw: dict
    source: str  # "llm" | "regex" | "regex_fallback"
    error: str | None = None

EXTRACTION_SYSTEM_PROMPT = (
    "You extract facts from free-text personal loan applications for an automated credit policy check.\n"
    "Return ONLY a JSON object with exactly these keys:\n"
    + "\n".join(f'- "{k}": {v}' for k, v in RAW_FIELDS.items())
    + "\n\nRules:\n"
    "- Use null for any fact that is not clearly stated. Never guess or infer missing values.\n"
    "- Numbers must be plain JSON numbers (no $, commas, % or 'k'; '$52k' -> 52000).\n"
    "- Convert employment duration to months ('2 years and 3 months' -> 27).\n"
    "- If income is given per month, fill monthly_income_usd and set annual_income_usd to null.\n"
    "- Rent, hobbies, family and how long someone has banked somewhere are NOT relevant facts.\n"
    "- Do not output names, gender, ethnicity or location."
)

class LLMExtractor:
    def __init__(self, client: LLMClient, fallback: "RegexExtractor | None" = None):
        self.client = client
        self.fallback = fallback

    def extract(self, narrative: str) -> ExtractionResult:
        messages = [
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": f"Application:\n\"\"\"\n{narrative}\n\"\"\""},
        ]
        try:
            data = self.client.chat_json(messages, max_tokens=400)
        except LLMError as exc:
            if self.fallback is None:
                raise
            result = self.fallback.extract(narrative)
            return ExtractionResult(result.raw, "regex_fallback", str(exc))
        return ExtractionResult({k: data.get(k) for k in RAW_FIELDS}, "llm")

_MONEY = re.compile(
    r"\$\s?(?P<a>\d[\d,]*(?:\.\d+)?)\s?(?P<ak>[kK]\b)?|(?P<b>\d[\d,]*(?:\.\d+)?)\s?(?P<bk>[kK]\b|dollars)"
)

def _money(text: str) -> list[float]:
    values = []
    for m in _MONEY.finditer(text):
        number = float((m.group("a") or m.group("b")).replace(",", ""))
        if m.group("ak") or (m.group("bk") or "").lower() == "k":
            number *= 1000
        values.append(number)
    return values

def _sentences(text: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?])\s+", text) if s]

def _first(pattern: str, text: str) -> re.Match | None:
    return re.search(pattern, text, flags=re.IGNORECASE)

class RegexExtractor:
    """Keyword/regex extractor tuned to common phrasings. Deliberately simple: it is the baseline."""

    def extract(self, narrative: str) -> ExtractionResult:
        raw: dict = {k: None for k in RAW_FIELDS}
        text = narrative

        for pattern in (r"\b(\d{1,3})[- ]years?[- ]old\b", r"\bage (\d{1,3})\b", r"\bI(?:'m| am) (\d{1,3})\b(?! (?:years?|months?) ago)"):
            if m := _first(pattern, text):
                raw["age"] = int(m.group(1))
                break

        for s in _sentences(text):
            lower = s.lower()
            is_loan = bool(re.search(r"borrow|requesting|personal loan", lower))
            if re.search(r"credit score|fico", lower) and raw["credit_score"] is None:
                scores = re.findall(r"\b(\d{3})\b", s)
                if scores:
                    raw["credit_score"] = int(scores[-1])
            if is_loan and raw["requested_amount_usd"] is None and (amounts := _money(s)):
                raw["requested_amount_usd"] = amounts[0]
            if re.search(r"\b(earn|earns|income|bring in)\b", lower) and not is_loan and (amounts := _money(s)):
                key = "monthly_income_usd" if "month" in lower else "annual_income_usd"
                raw[key] = amounts[0]
            if m := re.search(r"(?:debt-to-income ratio|dti) is ([\d.]+)\s?%", lower):
                raw["debt_to_income_ratio_percent"] = float(m.group(1))
            elif re.search(r"debt payments|existing debts|toward credit cards", lower) and not is_loan and (amounts := _money(s)):
                raw["monthly_debt_payments_usd"] = amounts[0]
            if re.search(r"role|employer|running this work", lower) and (duration := _duration_months(lower)) is not None:
                raw["current_employment_duration_months"] = duration

        if _first(r"full-time student", text):
            raw["employment_status"] = "student"
        elif _first(r"self-employed|works? for (?:myself|herself|himself)", text):
            raw["employment_status"] = "self_employed"
        elif _first(r"full-time", text):
            raw["employment_status"] = "employed_full_time"
        elif _first(r"part-time", text):
            raw["employment_status"] = "employed_part_time"
        elif _first(r"\bretired\b", text):
            raw["employment_status"] = "retired"
        elif _first(r"between jobs|unemployed|laid off", text):
            raw["employment_status"] = "unemployed"

        if _first(r"non-resident|not a US resident", text):
            raw["residency_status"] = "Non_Resident"
        elif _first(r"\bvisa\b", text):
            raw["residency_status"] = "Visa_Holder"
        elif _first(r"permanent resident|green card", text):
            raw["residency_status"] = "Permanent_Resident"
        elif _first(r"citizen", text):
            raw["residency_status"] = "US_Citizen"

        if _first(r"never filed for bankruptcy|no bankruptcies", text):
            raw["bankruptcy_filed"] = False
        elif m := _first(r"bankruptcy (\d+) years? ago", text):
            raw["bankruptcy_filed"] = True
            raw["bankruptcy_years_ago"] = int(m.group(1))

        if _first(r"(?:don't|does not currently) have a bank account|closed (?:my|her|his) bank account", text):
            raw["has_verifiable_bank_account"] = False
        elif _first(r"checking account", text):
            raw["has_verifiable_bank_account"] = True

        return ExtractionResult(raw, "regex")

def _duration_months(text: str) -> int | None:
    if m := re.search(r"for (\d+) years? and (\d+) months?", text):
        return int(m.group(1)) * 12 + int(m.group(2))
    if m := re.search(r"for (\d+) years?", text):
        return int(m.group(1)) * 12
    if m := re.search(r"for (\d+) months?", text):
        return int(m.group(1))
    return None
