from __future__ import annotations

from dataclasses import dataclass

from src.form_schema import GrantApplicationInput
from src.llm_client import LLMClient


@dataclass
class V2Result:
    failure_mode: str
    unknowns: str
    synthesis: str


def build_failure_mode_prompt(application: GrantApplicationInput) -> str:
    return (
        "You are analysing an FZlG grant application to identify the technical failure mode "
        "the project addresses.\n\n"
        f"Company: {application.company_name}\n"
        f"Business description: {application.company_description}\n"
        f"R&D project description: {application.project_description}\n\n"
        "Task: Identify and describe the specific failure mode in existing approaches that "
        "makes this project necessary. Name the existing methods or technologies that are "
        "insufficient and explain precisely how they fall short — not generally, but for the "
        "specific technical problem this project targets.\n\n"
        "80–120 words. Declarative prose. No headings or bullets."
    )


def build_unknowns_prompt(
    application: GrantApplicationInput, failure_mode: str
) -> str:
    return (
        "You are continuing to analyse an FZlG grant application.\n\n"
        f"Company: {application.company_name}\n"
        f"R&D project description: {application.project_description}\n\n"
        f"Failure mode already identified:\n{failure_mode}\n\n"
        "Task: Given this failure mode, articulate what the research team does not know at "
        "the project's outset — the specific technical questions they cannot answer without "
        "conducting the research. Under FZlG, technical uncertainty means the team lacks "
        "foreknowledge of whether their chosen approach will succeed, and what results it will "
        "produce. Be concrete: name the variables, parameters, or outcomes that are genuinely "
        "unknown before the project begins.\n\n"
        "80–120 words. Declarative prose. No headings or bullets."
    )


def build_synthesis_prompt(
    application: GrantApplicationInput, failure_mode: str, unknowns: str
) -> str:
    return (
        "You are writing the final Statement of Technical Uncertainty for an FZlG grant "
        "application to be submitted to the BSFZ.\n\n"
        f"Company: {application.company_name}\n"
        f"R&D project description: {application.project_description}\n\n"
        f"Failure mode in existing approaches:\n{failure_mode}\n\n"
        f"Technical unknowns at the project's outset:\n{unknowns}\n\n"
        "Task: Write the complete Statement of Technical Uncertainty. Integrate the failure "
        "mode, the unknowns, and the team's systematic R&D approach into a single flowing "
        "piece of formal prose. The statement must satisfy the BSFZ evaluation criteria: "
        "it must demonstrate that the project addresses genuine technical uncertainty — not "
        "routine product development — and that the team will pursue the work through a "
        "systematic, hypothesis-driven research process.\n\n"
        "Format rules:\n"
        "— 200–300 words\n"
        "— Declarative prose only; no bullets, no headings\n"
        "— Formal and specific throughout\n"
        "— No preamble\n\n"
        "If the project description reads as standard product engineering rather than "
        "systematic R&D, lead your response with this exact line before any other prose:\n"
        "⚠ This project may not qualify as R&D under FZlG — please review."
    )


def generate(application: GrantApplicationInput, llm: LLMClient) -> V2Result:
    failure_mode = llm.complete(
        build_failure_mode_prompt(application), max_tokens=300
    )
    unknowns = llm.complete(
        build_unknowns_prompt(application, failure_mode), max_tokens=300
    )
    synthesis = llm.complete(
        build_synthesis_prompt(application, failure_mode, unknowns), max_tokens=700
    )
    return V2Result(failure_mode=failure_mode, unknowns=unknowns, synthesis=synthesis)
