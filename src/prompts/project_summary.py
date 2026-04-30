from __future__ import annotations

from src.form_schema import GrantApplicationInput
from src.llm_client import LLMClient


def build_prompt(application: GrantApplicationInput) -> str:
    return (
        "Generate a project title and summary for the following FZlG grant application.\n\n"
        f"Company: {application.company_name}\n"
        f"Business description: {application.company_description}\n"
        f"R&D project description: {application.project_description}\n"
        f"R&D team: {application.team_size} people, "
        f"{application.rd_time_pct:.0f}% of working time on R&D\n"
        f"Claim year: {application.claim_year}\n\n"
        "Produce exactly two elements:\n"
        "1. A concise project title on the first line (no label, no colon prefix).\n"
        "2. Two to three paragraphs of BSFZ-grade project summary:\n"
        "   — Paragraph 1: the company context and the technical problem the R&D addresses.\n"
        "   — Paragraph 2: the specific technical uncertainty — what the team does not know at "
        "the project's outset and why existing approaches are insufficient.\n"
        "   — Paragraph 3 (include only if the description clearly supports it): the systematic "
        "research approach and what makes the work novel.\n\n"
        "No headings. No preamble. Title on line 1, blank line, then the paragraphs.\n"
        "Target length: 200–350 words total."
    )


def generate(application: GrantApplicationInput, llm: LLMClient) -> str:
    return llm.complete(build_prompt(application), max_tokens=600)
