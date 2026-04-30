from __future__ import annotations

from src.form_schema import GrantApplicationInput
from src.llm_client import LLMClient


def build_prompt(application: GrantApplicationInput) -> str:
    return (
        "Write a Statement of Technical Uncertainty for the following FZlG grant application.\n\n"
        f"Company: {application.company_name}\n"
        f"Business description: {application.company_description}\n"
        f"R&D project description: {application.project_description}\n"
        f"Claim year: {application.claim_year}\n\n"
        "The statement must cover all three of the following in flowing prose:\n"
        "1. The specific failure mode in existing methods that the project is trying to overcome — "
        "name the existing approaches and explain precisely how they fall short.\n"
        "2. What the team does not know at the project's outset and must discover — "
        "FZlG defines technical uncertainty as the lack of foreknowledge about whether "
        "a chosen approach will succeed.\n"
        "3. The team's systematic R&D approach — methods, hypotheses, and experimental process "
        "they will use to resolve the uncertainties.\n\n"
        "Format rules:\n"
        "— 150–300 words\n"
        "— Declarative prose only; no bullet points, no headings, no numbered lists\n"
        "— Formal and specific; name technologies, processes, and failure modes explicitly\n"
        "— No preamble (do not begin with 'This statement...' or 'The following...')\n\n"
        "If the project description reads as standard product engineering rather than systematic "
        "R&D, lead your response with this exact line before any other prose:\n"
        "⚠ This project may not qualify as R&D under FZlG — please review."
    )


def generate(application: GrantApplicationInput, llm: LLMClient) -> str:
    return llm.complete(build_prompt(application), max_tokens=600)
