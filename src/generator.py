from __future__ import annotations

from dataclasses import dataclass

from src.calculations import CostCalculation
from src.form_schema import GrantApplicationInput
from src.llm_client import LLMClient
from src.prompts import project_summary
from src.prompts import technical_uncertainty


@dataclass
class GeneratedDraft:
    project_summary: str
    technical_uncertainty: str
    # Phase 5: qualifying_activities: str
    # Phase 5: consultant_notes: str


def generate_draft(
    application: GrantApplicationInput,
    calc: CostCalculation,
    llm: LLMClient,
    *,
    uncertainty_version: str = "v2",
) -> GeneratedDraft:
    """Orchestrate LLM-generated sections. Deterministic math lives in calc."""
    return GeneratedDraft(
        project_summary=project_summary.generate(application, llm),
        technical_uncertainty=technical_uncertainty.generate(
            application, llm, version=uncertainty_version
        ),
    )
