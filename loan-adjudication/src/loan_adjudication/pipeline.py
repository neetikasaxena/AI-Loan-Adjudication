"""End-to-end adjudication: narrative -> extraction -> rules engine -> explanation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import DEFAULT_RULES_PATH
from .explainer import LLMExplainer, TemplateExplainer
from .extractor import LLMExtractor, RegexExtractor
from .llm_client import LLMClient
from .rules_engine import RulesEngine
from .schema import to_application

@dataclass
class Adjudicator:
    engine: RulesEngine
    extractor: LLMExtractor | RegexExtractor
    explainer: LLMExplainer | TemplateExplainer

    def run(self, narrative: str, application_id: str | None = None) -> dict:
        extraction = self.extractor.extract(narrative)
        application = to_application(extraction.raw)
        adjudication = self.engine.evaluate(application)
        explanation = self.explainer.explain(adjudication)
        return {
            "application_id": application_id,
            **explanation.to_dict(),
            "policy_version": adjudication.policy_version,
            "extracted_application": application,
            "extraction_source": extraction.source,
            "extraction_error": extraction.error,
        }

def build_adjudicator(extractor: str = "auto", explainer: str = "auto",
                      rules_path: str | Path = DEFAULT_RULES_PATH) -> Adjudicator:
    """extractor: auto|llm|regex, explainer: auto|llm|template. 'auto' uses the LLM when LLM_BASE_URL is set."""
    engine = RulesEngine.from_file(rules_path)
    needs_llm = "llm" in (extractor, explainer)
    client = LLMClient.from_env() if needs_llm or "auto" in (extractor, explainer) else None
    if needs_llm and client is None:
        raise SystemExit("LLM mode requested but LLM_BASE_URL is not configured (see .env.example).")

    use_llm_extractor = extractor == "llm" or (extractor == "auto" and client is not None)
    use_llm_explainer = explainer == "llm" or (explainer == "auto" and client is not None)
    return Adjudicator(
        engine=engine,
        extractor=LLMExtractor(client, fallback=RegexExtractor()) if use_llm_extractor else RegexExtractor(),
        explainer=LLMExplainer(client, engine) if use_llm_explainer else TemplateExplainer(),
    )
