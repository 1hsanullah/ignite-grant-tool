from __future__ import annotations

from dataclasses import dataclass

from src.calculations import CostCalculation
from src.form_schema import GrantApplicationInput
from src.llm_client import LLMClient
from src.prompts import project_summary
from src.prompts import technical_uncertainty
from src.prompts import qualifying_activities
from src.prompts import consultant_notes


@dataclass
class GeneratedDraft:
    project_summary: str
    technical_uncertainty: str
    qualifying_activities: str
    consultant_notes: str


def generate_draft(
    application: GrantApplicationInput,
    calc: CostCalculation,
    llm: LLMClient,
    *,
    uncertainty_version: str = "v2",
) -> GeneratedDraft:
    """Orchestrate LLM-generated sections. Deterministic math lives in calc."""
    summary = project_summary.generate(application, llm)
    uncertainty = technical_uncertainty.generate(
        application, llm, version=uncertainty_version
    )
    activities = qualifying_activities.generate(application, calc, llm)
    notes = consultant_notes.generate(
        application, calc, summary, uncertainty, activities, llm
    )
    return GeneratedDraft(
        project_summary=summary,
        technical_uncertainty=uncertainty,
        qualifying_activities=activities,
        consultant_notes=notes,
    )
