from loan_adjudication import DEFAULT_RULES_PATH
from loan_adjudication.explainer import TemplateExplainer, validate_explanation
from loan_adjudication.extractor import RegexExtractor
from loan_adjudication.features import FEATURE_NAMES, featurize
from loan_adjudication.rules_engine import RulesEngine
from loan_adjudication.schema import to_application
from loan_adjudication.synth import generate_dataset, to_dialogue_record, truth_application

ENGINE = RulesEngine.from_file(DEFAULT_RULES_PATH)

def app(**overrides) -> dict:
    applicant = {
        "age": 35, "credit_score": 720, "annual_income_usd": 60000.0, "debt_to_income_ratio_percent": 25.0,
        "employment_status": "employed_full_time", "current_employment_duration_months": 24,
        "residency_status": "US_Citizen", "has_bankruptcy_recent": False, "has_verifiable_bank_account": True,
    }
    requested = overrides.pop("requested_amount_usd", 10000.0)
    applicant.update(overrides)
    return {"applicant": applicant, "loan_application": {"requested_amount_usd": requested}}

def test_masked_narratives_and_dialogues_hide_identity():
    for rec in generate_dataset(100, seed=3):
        dialogue = to_dialogue_record(rec)
        for text in (rec["narrative_masked"], dialogue["narrative_masked"]):
            assert rec["identity"]["name"] not in text and rec["identity"]["city"] not in text
            assert not {" she ", " he ", " her ", " his "} & {f" {w.lower()} " for w in text.split()}

def test_dialogue_carries_the_same_facts_and_asks_about_withheld_ones():
    records = generate_dataset(300, seed=5, wording="train")
    exact = 0
    for rec in records:
        dialogue = to_dialogue_record(rec)
        assert dialogue["messages"][0]["role"] == "assistant" and dialogue["messages"][-1]["role"] == "user"
        if rec["profile"]["missing"]:
            assert any("manual review" in m["content"] or "policy check" in m["content"] for m in dialogue["messages"])
        exact += to_application(RegexExtractor().extract(dialogue["narrative"]).raw) == rec["truth"]
    assert exact / len(records) > 0.8

def test_reasoning_variants_differ_but_default_is_stable():
    adj = ENGINE.evaluate(app(credit_score=600))
    explainer = TemplateExplainer()
    assert explainer.reasoning(adj) == explainer.reasoning(adj)
    assert len({explainer.reasoning(adj, variant=v) for v in range(20)}) > 3

def test_clean_application_is_approved():
    assert ENGINE.evaluate(app()).decision == "APPROVE"

def test_thresholds_are_inclusive():
    assert ENGINE.evaluate(app(credit_score=670, debt_to_income_ratio_percent=40.0, age=18)).decision == "APPROVE"
    assert ENGINE.evaluate(app(credit_score=669)).decision == "REJECT"
    assert ENGINE.evaluate(app(requested_amount_usd=30000.0)).decision == "APPROVE"
    assert ENGINE.evaluate(app(requested_amount_usd=30001.0)).decision == "FLAG_REVIEW"

def test_reject_takes_precedence_over_review():
    adj = ENGINE.evaluate(app(has_verifiable_bank_account=False, current_employment_duration_months=3))
    assert adj.decision == "REJECT"
    assert adj.issue_ids == ["RULE-BANKACCTS-001", "RULE-EMPLOY-002"]

def test_missing_field_flags_review_and_tenure_not_applicable_for_retirees():
    assert ENGINE.evaluate(app(credit_score=None)).decision == "FLAG_REVIEW"
    retired = ENGINE.evaluate(app(employment_status="retired", current_employment_duration_months=None))
    assert retired.decision == "APPROVE"

def test_normalisation_derives_income_and_dti():
    application = to_application({"monthly_income_usd": 5000, "monthly_debt_payments_usd": "1,000",
                                  "bankruptcy_filed": True, "bankruptcy_years_ago": 9})
    assert application["applicant"]["annual_income_usd"] == 60000
    assert application["applicant"]["debt_to_income_ratio_percent"] == 20.0
    assert application["applicant"]["has_bankruptcy_recent"] is False

def test_generator_is_reproducible_and_regex_extracts_most_records():
    records = generate_dataset(200, seed=7, wording="train")
    assert records == generate_dataset(200, seed=7, wording="train")
    exact = sum(to_application(RegexExtractor().extract(r["narrative"]).raw) == truth_application(r["profile"])
                for r in records)
    assert exact / len(records) > 0.8

def test_heldout_wordings_never_appear_in_training_text():
    train_texts = " ".join(r["narrative"] for r in generate_dataset(300, seed=11, wording="train"))
    val_texts = " ".join(r["narrative"] for r in generate_dataset(300, seed=11, wording="val"))
    for phrase in ("My salary is", "FICO comes in at", "looking to finance", "no history of bankruptcy"):
        assert phrase not in train_texts and phrase in val_texts

def test_features_encode_missing_values_with_flags():
    row = featurize(app(credit_score=None))
    names = dict(zip(FEATURE_NAMES, row))
    assert len(row) == len(FEATURE_NAMES)
    assert names["credit_score"] == -1.0 and names["credit_score_missing"] == 1.0
    assert names["loan_to_income"] == 10000.0 / 60000.0

def test_guardrail_rejects_wrong_decision_and_protected_terms():
    adj = ENGINE.evaluate(app(credit_score=600))
    good = {"decision": "REJECT", "failed_rules": ["RULE-CREDIT-001"],
            "reasoning": "Your credit score of 600 is below the minimum of 670 required for this loan."}
    assert validate_explanation(good, adj) == []
    assert validate_explanation({**good, "decision": "APPROVE"}, adj)
    assert validate_explanation({**good, "reasoning": good["reasoning"] + " Being female did not matter."}, adj)
