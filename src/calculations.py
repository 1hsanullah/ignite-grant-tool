from __future__ import annotations

from dataclasses import dataclass

from src.form_schema import GrantApplicationInput

# FZlG constants — per Forschungszulagengesetz and Ignite's spec
SME_CREDIT_RATE: float = 0.35
NON_SME_CREDIT_RATE: float = 0.25
SME_REVENUE_THRESHOLD: float = 35_000_000  # annual revenue threshold (€)
ELIGIBLE_COST_CAP: float = 3_500_000       # maximum eligible costs per year (€)
CONTRACTOR_ELIGIBLE_FRACTION: float = 0.60  # only 60% of contractor costs qualify
CAPEX_ELIGIBLE_FROM_YEAR: int = 2024        # capital expenditure became eligible in 2024


@dataclass(frozen=True)
class CostCalculation:
    eligible_personnel: float
    eligible_contractor: float    # already multiplied by 0.60
    eligible_capex: float         # 0 if claim_year < 2024
    total_eligible_before_cap: float
    total_eligible: float         # capped at ELIGIBLE_COST_CAP
    is_capped: bool
    is_sme: bool
    revenue_unknown: bool         # True when annual revenue wasn't provided
    credit_rate: float            # 0.35 (SME) or 0.25 (non-SME)
    indicative_credit: float      # total_eligible × credit_rate
    capex_excluded: bool          # True when capex entered but claim_year < 2024


def calculate(application: GrantApplicationInput) -> CostCalculation:
    is_sme = application.is_sme
    revenue_unknown = application.annual_revenue_eur is None

    eligible_personnel = application.personnel_cost_eur
    eligible_contractor = round(
        application.contractor_cost_eur * CONTRACTOR_ELIGIBLE_FRACTION, 2
    )

    capex_excluded = (
        application.capex_cost_eur > 0
        and application.claim_year < CAPEX_ELIGIBLE_FROM_YEAR
    )
    eligible_capex = (
        application.capex_cost_eur
        if application.claim_year >= CAPEX_ELIGIBLE_FROM_YEAR
        else 0.0
    )

    total_before_cap = eligible_personnel + eligible_contractor + eligible_capex
    is_capped = total_before_cap > ELIGIBLE_COST_CAP
    total_eligible = min(total_before_cap, ELIGIBLE_COST_CAP)

    credit_rate = SME_CREDIT_RATE if is_sme else NON_SME_CREDIT_RATE
    indicative_credit = round(total_eligible * credit_rate, 2)

    return CostCalculation(
        eligible_personnel=eligible_personnel,
        eligible_contractor=eligible_contractor,
        eligible_capex=eligible_capex,
        total_eligible_before_cap=total_before_cap,
        total_eligible=total_eligible,
        is_capped=is_capped,
        is_sme=is_sme,
        revenue_unknown=revenue_unknown,
        credit_rate=credit_rate,
        indicative_credit=indicative_credit,
        capex_excluded=capex_excluded,
    )
