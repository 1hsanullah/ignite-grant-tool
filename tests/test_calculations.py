from datetime import date

import pytest

from src.calculations import (
    CAPEX_ELIGIBLE_FROM_YEAR,
    ELIGIBLE_COST_CAP,
    NON_SME_CREDIT_RATE,
    SME_CREDIT_RATE,
    SME_REVENUE_THRESHOLD,
    calculate,
)
from src.form_schema import GrantApplicationInput

CURRENT_YEAR = date.today().year


def make_input(**overrides) -> GrantApplicationInput:
    defaults = {
        "company_name": "Test GmbH",
        "company_description": "A software company doing R&D",
        "project_description": "A" * 60,  # satisfies min_length=50
        "team_size": 5,
        "rd_time_pct": 80.0,
        "annual_revenue_eur": None,
        "personnel_cost_eur": 100_000.0,
        "contractor_cost_eur": 0.0,
        "capex_cost_eur": 0.0,
        "claim_year": CURRENT_YEAR,
    }
    defaults.update(overrides)
    return GrantApplicationInput(**defaults)


# ── SME detection ──────────────────────────────────────────────────────────────

def test_sme_below_threshold():
    result = calculate(make_input(annual_revenue_eur=SME_REVENUE_THRESHOLD - 1))
    assert result.is_sme is True
    assert result.credit_rate == SME_CREDIT_RATE


def test_sme_at_threshold_is_non_sme():
    # Threshold is strict <, so exactly €35M is non-SME
    result = calculate(make_input(annual_revenue_eur=SME_REVENUE_THRESHOLD))
    assert result.is_sme is False
    assert result.credit_rate == NON_SME_CREDIT_RATE


def test_non_sme_above_threshold():
    result = calculate(make_input(annual_revenue_eur=50_000_000))
    assert result.is_sme is False
    assert result.credit_rate == NON_SME_CREDIT_RATE


def test_revenue_unknown_defaults_to_non_sme():
    result = calculate(make_input(annual_revenue_eur=None))
    assert result.is_sme is False
    assert result.revenue_unknown is True
    assert result.credit_rate == NON_SME_CREDIT_RATE


# ── Cost eligibility rules ─────────────────────────────────────────────────────

def test_personnel_fully_eligible():
    result = calculate(make_input(personnel_cost_eur=200_000))
    assert result.eligible_personnel == 200_000.0


def test_contractor_sixty_percent_eligible():
    result = calculate(make_input(contractor_cost_eur=100_000, personnel_cost_eur=0))
    assert result.eligible_contractor == 60_000.0


def test_contractor_zero_stays_zero():
    result = calculate(make_input(contractor_cost_eur=0))
    assert result.eligible_contractor == 0.0


def test_capex_excluded_before_2024():
    # 2023 is valid (within 4-year window until 2027); capex must be zeroed
    result = calculate(make_input(capex_cost_eur=50_000, personnel_cost_eur=0, claim_year=2023))
    assert result.eligible_capex == 0.0
    assert result.capex_excluded is True


def test_capex_eligible_from_2024():
    result = calculate(make_input(capex_cost_eur=50_000, personnel_cost_eur=0, claim_year=2024))
    assert result.eligible_capex == 50_000.0
    assert result.capex_excluded is False


def test_capex_zero_not_flagged_as_excluded():
    result = calculate(make_input(capex_cost_eur=0, claim_year=2023))
    assert result.capex_excluded is False


# ── Annual cap ─────────────────────────────────────────────────────────────────

def test_cap_applied_above_limit():
    result = calculate(make_input(personnel_cost_eur=ELIGIBLE_COST_CAP + 1))
    assert result.is_capped is True
    assert result.total_eligible == ELIGIBLE_COST_CAP


def test_cap_not_applied_at_exactly_limit():
    # Exactly at the cap: not capped (strict > check)
    result = calculate(make_input(personnel_cost_eur=ELIGIBLE_COST_CAP))
    assert result.is_capped is False
    assert result.total_eligible == ELIGIBLE_COST_CAP


def test_cap_not_applied_below_limit():
    result = calculate(make_input(personnel_cost_eur=1_000_000))
    assert result.is_capped is False
    assert result.total_eligible == 1_000_000.0


# ── Credit calculation ─────────────────────────────────────────────────────────

def test_credit_sme():
    result = calculate(make_input(annual_revenue_eur=10_000_000, personnel_cost_eur=1_000_000))
    assert result.indicative_credit == pytest.approx(350_000.0)


def test_credit_non_sme():
    result = calculate(make_input(annual_revenue_eur=50_000_000, personnel_cost_eur=1_000_000))
    assert result.indicative_credit == pytest.approx(250_000.0)


def test_credit_applies_to_capped_total():
    # Eligible costs exceed cap; credit is on capped amount
    result = calculate(
        make_input(annual_revenue_eur=10_000_000, personnel_cost_eur=5_000_000)
    )
    assert result.total_eligible == ELIGIBLE_COST_CAP
    assert result.indicative_credit == pytest.approx(ELIGIBLE_COST_CAP * SME_CREDIT_RATE)


# ── Combined scenario ──────────────────────────────────────────────────────────

def test_combined_costs_sme():
    result = calculate(
        make_input(
            annual_revenue_eur=10_000_000,  # SME
            personnel_cost_eur=500_000,
            contractor_cost_eur=100_000,   # → 60,000 eligible
            capex_cost_eur=50_000,          # eligible (current year >= 2024)
            claim_year=CURRENT_YEAR,
        )
    )
    assert result.eligible_personnel == 500_000.0
    assert result.eligible_contractor == 60_000.0
    assert result.eligible_capex == 50_000.0
    assert result.total_eligible_before_cap == 610_000.0
    assert result.total_eligible == 610_000.0
    assert result.is_capped is False
    assert result.indicative_credit == pytest.approx(610_000.0 * SME_CREDIT_RATE)
