from __future__ import annotations

from src.calculations import CostCalculation, calculate
from src.form_schema import GrantApplicationInput
from src.prompts import consultant_notes


def _make_application(**overrides) -> GrantApplicationInput:
    defaults = {
        "company_name": "Acme GmbH",
        "company_description": "A German tech company.",
        "project_description": "A" * 60,
        "team_size": 3,
        "rd_time_pct": 80,
        "annual_revenue_eur": None,
        "personnel_cost_eur": 100_000,
        "contractor_cost_eur": 0,
        "capex_cost_eur": 0,
        "claim_year": 2025,
    }
    defaults.update(overrides)
    return GrantApplicationInput(**defaults)


# ── build_prompt ────────────────────────────────────────────────────────────────

def test_build_prompt_threads_project_summary():
    app = _make_application()
    prompt = consultant_notes.build_prompt(app, "THE SUMMARY TEXT", "tech uncertainty", "activities")
    assert "THE SUMMARY TEXT" in prompt


def test_build_prompt_threads_technical_uncertainty():
    app = _make_application()
    prompt = consultant_notes.build_prompt(app, "summary", "UNCERTAINTY TEXT HERE", "activities")
    assert "UNCERTAINTY TEXT HERE" in prompt


def test_build_prompt_threads_qualifying_activities():
    app = _make_application()
    prompt = consultant_notes.build_prompt(app, "summary", "uncertainty", "ACTIVITIES TEXT HERE")
    assert "ACTIVITIES TEXT HERE" in prompt


def test_build_prompt_includes_verify_category():
    app = _make_application()
    prompt = consultant_notes.build_prompt(app, "s", "u", "a")
    assert "[Verify]" in prompt


def test_build_prompt_includes_weakness_category():
    app = _make_application()
    prompt = consultant_notes.build_prompt(app, "s", "u", "a")
    assert "[Weakness]" in prompt


def test_build_prompt_includes_strengthen_category():
    app = _make_application()
    prompt = consultant_notes.build_prompt(app, "s", "u", "a")
    assert "[Strengthen]" in prompt


def test_build_prompt_includes_company_name():
    app = _make_application(company_name="BetaCorp GmbH")
    prompt = consultant_notes.build_prompt(app, "s", "u", "a")
    assert "BetaCorp GmbH" in prompt


def test_build_prompt_includes_project_description():
    app = _make_application(project_description="Z" * 60)
    prompt = consultant_notes.build_prompt(app, "s", "u", "a")
    assert "Z" * 60 in prompt


# ── deterministic_notes ─────────────────────────────────────────────────────────

def test_deterministic_notes_revenue_unknown():
    app = _make_application(annual_revenue_eur=None)
    calc = calculate(app)
    notes = consultant_notes.deterministic_notes(app, calc)
    assert any("[Verify]" in n and "revenue" in n.lower() for n in notes)


def test_deterministic_notes_no_flag_when_revenue_known():
    app = _make_application(annual_revenue_eur=10_000_000)
    calc = calculate(app)
    notes = consultant_notes.deterministic_notes(app, calc)
    assert not any("revenue" in n.lower() and "not provided" in n.lower() for n in notes)


def test_deterministic_notes_capex_excluded():
    app = _make_application(capex_cost_eur=50_000, claim_year=2023)
    calc = calculate(app)
    notes = consultant_notes.deterministic_notes(app, calc)
    assert any("capex" in n.lower() or "capital" in n.lower() for n in notes)


def test_deterministic_notes_capex_eligible_not_flagged():
    app = _make_application(capex_cost_eur=50_000, claim_year=2024)
    calc = calculate(app)
    notes = consultant_notes.deterministic_notes(app, calc)
    assert not any("excluded" in n.lower() and "capital" in n.lower() for n in notes)


def test_deterministic_notes_is_capped():
    app = _make_application(personnel_cost_eur=4_000_000)
    calc = calculate(app)
    notes = consultant_notes.deterministic_notes(app, calc)
    assert any("cap" in n.lower() or "3,500,000" in n for n in notes)


def test_deterministic_notes_contractor_flag():
    app = _make_application(contractor_cost_eur=80_000)
    calc = calculate(app)
    notes = consultant_notes.deterministic_notes(app, calc)
    assert any("contractor" in n.lower() for n in notes)


def test_deterministic_notes_empty_for_clean_application():
    app = _make_application(
        annual_revenue_eur=10_000_000,  # known SME
        capex_cost_eur=0,
        contractor_cost_eur=0,
        personnel_cost_eur=200_000,     # well under cap
        claim_year=2025,
    )
    calc = calculate(app)
    notes = consultant_notes.deterministic_notes(app, calc)
    assert notes == []
