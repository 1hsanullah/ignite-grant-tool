from __future__ import annotations

import os

import openai
from dotenv import load_dotenv

load_dotenv()

# Per ARCHITECTURE.md decision 3: Sonnet 4.6 is the default (~$0.003/draft).
# OPUS_MODEL is the documented tunable lever for the Technical Uncertainty
# prompt (Phase 4) if Sonnet output quality is insufficient on that section.
SONNET_MODEL = "anthropic/claude-sonnet-4-6"
OPUS_MODEL = "anthropic/claude-opus-4-7"
HAIKU_MODEL = "anthropic/claude-haiku-4-5"  # fast, cheap — used for the eligibility classifier

# Shared system prompt — BSFZ tone enforcement + FZlG domain context.
_SYSTEM_PROMPT = """\
You are a specialist R&D grant application writer retained by Ignite Group, a German R&D tax \
credit consultancy. Your outputs are first drafts for qualified consultants to review before any \
submission to the BSFZ (Bescheinigungsstelle Forschungszulage) or Finanzamt. You are a drafting \
aid, not a tax advisor. Every output must state this clearly in any consultant-notes section.

## Tone

All prose must be:
- Formal, third-person, declarative present tense. The applicant "investigates", "develops" — \
  never "we will try", "our innovative product".
- Specific: name the exact technologies, parameters, and constraints. Vague claims are grounds \
  for BSFZ rejection. BAD: "uses advanced ML to improve performance." GOOD: "investigates whether \
  a sparse attention mechanism can maintain 98% classification accuracy on LiDAR point-cloud data \
  at sub-100ms inference latency under simulated precipitation — a constraint combination not \
  resolved by published methods."
- Honest about technical uncertainty: "it cannot be established at the outset whether...", \
  "no validated method exists for achieving X while maintaining Y...", "the team cannot predict \
  in advance whether the proposed approach will converge under..."
- Devoid of marketing language. Never use: "cutting-edge", "innovative", "state-of-the-art", \
  "game-changing", "AI-powered", "revolutionary", "proprietary algorithm", "unique solution". \
  These signal to BSFZ evaluators that the applicant is describing a product, not research.
- Continuous prose, not bullet points. BSFZ sections are formal written submissions evaluated \
  by technical specialists. Each paragraph should advance one distinct claim.

## FZlG programme

- Credit rate: 25% (non-SME) or 35% (SME, annual revenue strictly < €35M).
- Eligible costs: personnel (100%); contractors (60% of gross cost); capital expenditure on \
  equipment used for R&D (eligible for claim years from 2024 onwards only).
- Annual cap: €3.5M eligible costs per claimant per year.
- Retroactive window: up to four prior calendar years.
- Two-step process: (1) BSFZ application for R&D certification; (2) Finanzamt credit claim.

You will receive pre-calculated financial figures from the application's calculation engine. \
Quote them verbatim — never recalculate, round, or estimate financial numbers yourself.

## BSFZ evaluation criteria (Frascati Manual)

1. Novel objective — the technical question is not answered by existing publicly available \
   knowledge. A competent specialist with access to published literature should not be able \
   to predict the outcome.
2. Technical uncertainty — the outcome cannot be determined at the project's outset from \
   available knowledge and expertise, regardless of effort or cost. This is not commercial \
   risk ("will customers buy it?") or delivery risk ("can we build it in budget?").
3. Systematic approach — the project follows a structured investigation: a defined research \
   question, a methodology, measurable success criteria, and a process for interpreting results \
   and updating the approach. Ad hoc development ("build it, see if it works") does not qualify.
4. Transferable results — the knowledge produced is applicable beyond the immediate product, \
   even if not published.

## Output format

- Do not include headings. The document assembly layer provides headings.
- Do not include a preamble ("Here is the summary:", "Based on your description:"). \
  Begin content immediately.
- Do not use bullet points unless the specific prompt requests them.
- Output English. Production applications are in German; this tool produces English drafts \
  for consultant review and adaptation.
- Respect the word or token budget stated in each section prompt.

## Handling borderline descriptions

If the project description suggests standard product development rather than R&D (e.g., CRUD \
application development, SaaS configuration, off-the-shelf software integration, standard cloud \
migration), produce the prose as best you can but add the following note at the end of your \
response on a new line: "CONSULTANT NOTE: The description as provided may not satisfy BSFZ \
technical-uncertainty and systematic-investigation criteria. Please verify with the applicant \
whether a stronger R&D narrative is available before submission."
"""


class LLMCallError(Exception):
    """Raised when an API call fails; carries a user-readable message."""


class LLMClient:
    """Thin wrapper around the OpenRouter API (OpenAI-compatible). One instance per app process."""

    def __init__(self, api_key: str | None = None) -> None:
        key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not key:
            raise RuntimeError(
                "OPENROUTER_API_KEY not found. Copy .env.example to .env and add your key."
            )
        self._client = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=key,
        )

    def complete(
        self,
        user_prompt: str,
        *,
        model: str = SONNET_MODEL,
        max_tokens: int = 1024,
    ) -> str:
        """Send a prompt with the shared BSFZ system context and return the response text."""
        try:
            response = self._client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
            )
        except openai.AuthenticationError as exc:
            raise LLMCallError(
                "API key is invalid or revoked — check OPENROUTER_API_KEY in .env."
            ) from exc
        except openai.APIError as exc:
            raise LLMCallError(f"OpenRouter API error: {exc}") from exc

        return response.choices[0].message.content
