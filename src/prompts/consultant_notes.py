from __future__ import annotations

from src.calculations import CostCalculation
from src.form_schema import GrantApplicationInput
from src.llm_client import LLMClient


def deterministic_notes(application: GrantApplicationInput, calc: CostCalculation) -> list[str]:
    """Return factual flags derived from calc — these are certain, so never delegated to LLM."""
    notes: list[str] = []
    if calc.revenue_unknown:
        notes.append(
            "[Verify] Annual revenue was not provided — credit rate defaulted to 25% (non-SME). "
            "If the company qualifies as an SME (<€35M revenue), the rate rises to 35% and should "
            "be corrected before submission."
        )
    if calc.capex_excluded:
        notes.append(
            f"[Verify] Capital expenditure of €{application.capex_cost_eur:,.0f} was entered but "
            f"claim year {application.claim_year} is before 2024 — capex is ineligible under FZlG "
            "for this period. Confirm the year or remove capex from the claim."
        )
    if calc.is_capped:
        notes.append(
            f"[Verify] Total eligible costs (€{calc.total_eligible_before_cap:,.0f}) exceed the "
            "annual FZlG cap of €3,500,000. The credit is calculated on €3,500,000. If the company "
            "has multiple distinct R&D projects, consider whether they should be filed separately."
        )
    if application.contractor_cost_eur > 0:
        notes.append(
            f"[Verify] Contractor costs of €{application.contractor_cost_eur:,.0f} are included. "
            "Under FZlG only 60% is eligible (= €{:.0f}). Ensure subcontractor invoices clearly ".format(
                calc.eligible_contractor
            ) +
            "reference the qualifying R&D project and that the relationship meets BSFZ requirements "
            "(the work must be conducted on behalf of the claimant)."
        )
    return notes


def build_prompt(
    application: GrantApplicationInput,
    project_summary: str,
    technical_uncertainty: str,
    qualifying_activities: str,
) -> str:
    return (
        "You are reviewing a first-draft FZlG grant application to produce notes for the "
        "consultant who will finalise and submit it. You wrote the draft — you are now reviewing "
        "your own output for weaknesses, gaps, and items that need verification.\n\n"
        "=== DRAFT SECTIONS ===\n\n"
        f"PROJECT SUMMARY:\n{project_summary}\n\n"
        f"STATEMENT OF TECHNICAL UNCERTAINTY:\n{technical_uncertainty}\n\n"
        f"QUALIFYING R&D ACTIVITIES:\n{qualifying_activities}\n\n"
        "=== ORIGINAL INPUT ===\n\n"
        f"Company: {application.company_name}\n"
        f"Business description: {application.company_description}\n"
        f"R&D project description: {application.project_description}\n"
        f"Team: {application.team_size} people, {application.rd_time_pct:.0f}% on R&D\n"
        f"Claim year: {application.claim_year}\n\n"
        "=== YOUR TASK ===\n\n"
        "Produce a bulleted list of consultant notes. Each bullet must be one of:\n"
        "— [Verify] Something the consultant must fact-check before submission "
        "(e.g. specific technology claims, team qualifications, prior art statements).\n"
        "— [Weakness] A part of the draft that reads thin, generic, or risks looking like "
        "product engineering rather than systematic R&D to a BSFZ evaluator.\n"
        "— [Strengthen] A concrete addition that would materially improve the application "
        "(e.g. a failed-experiment scenario the client should be asked about, "
        "missing documentation of systematic method, prior art references to name).\n\n"
        "Rules:\n"
        "— 5–10 bullets total.\n"
        "— Be specific — name the sentence or claim you are flagging.\n"
        "— Do not praise the draft. Only flag things that need attention.\n"
        "— No preamble. No summary. Bullets only."
    )


def generate(
    application: GrantApplicationInput,
    calc: CostCalculation,
    project_summary: str,
    technical_uncertainty: str,
    qualifying_activities: str,
    llm: LLMClient,
) -> str:
    fixed = deterministic_notes(application, calc)
    llm_notes = llm.complete(
        build_prompt(application, project_summary, technical_uncertainty, qualifying_activities),
        max_tokens=700,
    )
    if fixed:
        return "\n".join(f"- {note}" for note in fixed) + "\n" + llm_notes
    return llm_notes
