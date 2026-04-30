from __future__ import annotations

import re

from src.form_schema import GrantApplicationInput
from src.llm_client import HAIKU_MODEL, LLMCallError, LLMClient

_SCORE_RE = re.compile(r"Score:\s*([1-5])", re.IGNORECASE)
_REASONING_RE = re.compile(r"Reasoning:\s*(.+)", re.IGNORECASE | re.DOTALL)


def build_prompt(application: GrantApplicationInput) -> str:
    return (
        "Classify the following project description on the FZlG R&D scale.\n\n"
        f"Company: {application.company_name}\n"
        f"Business: {application.company_description}\n"
        f"Project: {application.project_description}\n\n"
        "Score the project on a scale of 1–5 using Frascati Manual criteria:\n"
        "5 — Clear R&D: genuine technical uncertainty, systematic investigative approach, "
        "novel objective not answerable from published knowledge, transferable results.\n"
        "4 — Likely R&D: strong indicators of technical uncertainty and systematic method, "
        "minor gaps in description.\n"
        "3 — Borderline: significant technical complexity but unclear whether uncertainty is "
        "technical (qualifying) or commercial/delivery (non-qualifying).\n"
        "2 — Unlikely R&D: mostly product engineering; uses known methods for a known outcome; "
        "limited evidence of systematic investigation.\n"
        "1 — Not R&D: clear product development, CRUD application, SaaS configuration, "
        "off-the-shelf software integration, or standard cloud migration.\n\n"
        "Respond with exactly two lines:\n"
        "Score: <integer 1–5>\n"
        "Reasoning: <one concise paragraph — name the specific signals that drove your score>"
    )


def _parse_score_and_reasoning(raw: str) -> tuple[int, str]:
    score_match = _SCORE_RE.search(raw)
    reasoning_match = _REASONING_RE.search(raw)
    if not score_match:
        return 3, raw.strip()
    score = int(score_match.group(1))
    reasoning = reasoning_match.group(1).strip() if reasoning_match else raw.strip()
    return score, reasoning


def generate(application: GrantApplicationInput, llm: LLMClient) -> tuple[int, str]:
    """Return (score 1–5, reasoning paragraph). Falls back to (3, message) on API failure."""
    try:
        raw = llm.complete(build_prompt(application), model=HAIKU_MODEL, max_tokens=300)
        return _parse_score_and_reasoning(raw)
    except LLMCallError:
        return 3, "Classifier unavailable — defaulted to Needs Review."
