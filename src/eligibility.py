from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal

from src.calculations import CostCalculation
from src.form_schema import GrantApplicationInput
from src.llm_client import LLMClient
from src.prompts import rd_classifier


class Verdict(str, Enum):
    ELIGIBLE = "Eligible"
    NEEDS_REVIEW = "Needs Review"
    LIKELY_INELIGIBLE = "Likely Ineligible"


@dataclass(frozen=True)
class Check:
    name: str
    status: Literal["pass", "warn", "fail"]
    reasoning: str


@dataclass(frozen=True)
class EligibilityResult:
    verdict: Verdict
    checks: list[Check]
    rd_score: int        # 1–5 from the LLM classifier
    rd_reasoning: str


def _check_germany(application: GrantApplicationInput) -> Check:
    if application.is_germany_registered is True:
        return Check(
            name="German taxable presence",
            status="pass",
            reasoning="Company confirmed as registered (taxable) in Germany — meets the FZlG jurisdictional requirement.",
        )
    if application.is_germany_registered is False:
        return Check(
            name="German taxable presence",
            status="fail",
            reasoning=(
                "FZlG is restricted to entities with a German taxable presence (Betriebsstätte). "
                "Verify with the client whether a German legal entity or permanent establishment exists."
            ),
        )
    return Check(
        name="German taxable presence",
        status="warn",
        reasoning=(
            "German registration not confirmed — FZlG requires a German taxable presence. "
            "Obtain confirmation of Betriebsstätte status before submission."
        ),
    )


def _check_cost_cap(calc: CostCalculation) -> Check:
    if calc.is_capped:
        return Check(
            name="Cost figures within FZlG limits",
            status="warn",
            reasoning=(
                f"Total eligible costs (€{calc.total_eligible_before_cap:,.0f}) exceed the "
                "annual FZlG cap of €3,500,000. The credit is calculated on the capped amount. "
                "This does not disqualify the application but limits the credit."
            ),
        )
    return Check(
        name="Cost figures within FZlG limits",
        status="pass",
        reasoning=f"Total eligible costs (€{calc.total_eligible:,.0f}) are within the €3,500,000 annual cap.",
    )


def _check_claim_year(application: GrantApplicationInput) -> Check:
    return Check(
        name="Claim year within retroactive window",
        status="pass",
        reasoning=(
            f"Claim year {application.claim_year} is within the FZlG four-year retroactive window "
            "(validated at input)."
        ),
    )


def _check_rd_classification(rd_score: int, rd_reasoning: str) -> Check:
    if rd_score >= 4:
        return Check(
            name="R&D vs product-engineering classification",
            status="pass",
            reasoning=f"R&D score {rd_score}/5. {rd_reasoning}",
        )
    if rd_score == 3:
        return Check(
            name="R&D vs product-engineering classification",
            status="warn",
            reasoning=(
                f"R&D score {rd_score}/5 — borderline. {rd_reasoning} "
                "Strengthen the description of technical uncertainty and systematic method before submission."
            ),
        )
    return Check(
        name="R&D vs product-engineering classification",
        status="fail",
        reasoning=(
            f"R&D score {rd_score}/5 — project appears to be product engineering rather than R&D. "
            f"{rd_reasoning} "
            "Review whether genuine technical uncertainty can be articulated. If not, FZlG certification is unlikely."
        ),
    )


def _aggregate_verdict(checks: list[Check]) -> Verdict:
    statuses = {c.status for c in checks}
    if "fail" in statuses:
        return Verdict.LIKELY_INELIGIBLE
    if "warn" in statuses:
        return Verdict.NEEDS_REVIEW
    return Verdict.ELIGIBLE


def evaluate(
    application: GrantApplicationInput,
    calc: CostCalculation,
    llm: LLMClient,
) -> EligibilityResult:
    rd_score, rd_reasoning = rd_classifier.generate(application, llm)

    checks = [
        _check_germany(application),
        _check_cost_cap(calc),
        _check_claim_year(application),
        _check_rd_classification(rd_score, rd_reasoning),
    ]

    return EligibilityResult(
        verdict=_aggregate_verdict(checks),
        checks=checks,
        rd_score=rd_score,
        rd_reasoning=rd_reasoning,
    )
