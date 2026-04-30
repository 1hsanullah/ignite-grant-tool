from __future__ import annotations

from src.calculations import CostCalculation
from src.form_schema import GrantApplicationInput
from src.llm_client import LLMClient


def build_prompt(application: GrantApplicationInput, calc: CostCalculation) -> str:
    cost_context = (
        f"Personnel: €{application.personnel_cost_eur:,.0f} (100% eligible)\n"
        f"Contractors: €{application.contractor_cost_eur:,.0f} (60% eligible = €{calc.eligible_contractor:,.0f})\n"
        f"Equipment/capex: €{application.capex_cost_eur:,.0f}"
        f"{' (excluded — claim year is pre-2024)' if calc.capex_excluded else ' (eligible from 2024)'}\n"
        f"Claim year: {application.claim_year}"
    )
    return (
        "List the qualifying R&D activities for the following FZlG grant application.\n\n"
        f"Company: {application.company_name}\n"
        f"Business description: {application.company_description}\n"
        f"R&D project description: {application.project_description}\n"
        f"R&D team: {application.team_size} people, {application.rd_time_pct:.0f}% on R&D\n"
        f"Costs:\n{cost_context}\n\n"
        "Produce a numbered list of 6–10 qualifying R&D activities drawn directly from "
        "the project description. Each item must:\n"
        "— Be one declarative sentence (no sub-bullets).\n"
        "— Name the specific technical activity (e.g. 'Design and execution of controlled "
        "experiments to determine…', 'Systematic evaluation of alternative architectures…').\n"
        "— Classify it in parentheses as one of: (Experimental development), "
        "(Applied research), or (Fundamental research).\n"
        "— Relate directly to the technical challenge described — no generic filler.\n\n"
        "No preamble. No headings. Numbered list only.\n"
        "If the project description contains activities that are routine product engineering "
        "rather than R&D, omit them — list only activities with genuine technical uncertainty."
    )


def generate(application: GrantApplicationInput, calc: CostCalculation, llm: LLMClient) -> str:
    return llm.complete(build_prompt(application, calc), max_tokens=650)
