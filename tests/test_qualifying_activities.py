from __future__ import annotations

from src.calculations import calculate
from src.form_schema import GrantApplicationInput
from src.prompts import qualifying_activities


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


def test_build_prompt_includes_project_description():
    app = _make_application(project_description="X" * 60)
    calc = calculate(app)
    assert "X" * 60 in qualifying_activities.build_prompt(app, calc)


def test_build_prompt_includes_company_name():
    app = _make_application(company_name="TestCo GmbH")
    calc = calculate(app)
    assert "TestCo GmbH" in qualifying_activities.build_prompt(app, calc)


def test_build_prompt_includes_activity_categories():
    app = _make_application()
    calc = calculate(app)
    prompt = qualifying_activities.build_prompt(app, calc)
    assert "Experimental development" in prompt
    assert "Applied research" in prompt
    assert "Fundamental research" in prompt


def test_build_prompt_requests_numbered_list():
    app = _make_application()
    calc = calculate(app)
    prompt = qualifying_activities.build_prompt(app, calc)
    assert "numbered list" in prompt.lower() or "6–10" in prompt


def test_build_prompt_includes_cost_context():
    app = _make_application(personnel_cost_eur=200_000, contractor_cost_eur=50_000)
    calc = calculate(app)
    prompt = qualifying_activities.build_prompt(app, calc)
    assert "200,000" in prompt
    assert "50,000" in prompt


def test_build_prompt_notes_capex_excluded_for_pre_2024():
    app = _make_application(capex_cost_eur=30_000, claim_year=2023)
    calc = calculate(app)
    prompt = qualifying_activities.build_prompt(app, calc)
    assert "pre-2024" in prompt or "excluded" in prompt.lower()


def test_build_prompt_does_not_flag_capex_for_2024():
    app = _make_application(capex_cost_eur=30_000, claim_year=2024)
    calc = calculate(app)
    prompt = qualifying_activities.build_prompt(app, calc)
    assert "excluded" not in prompt.lower() or "pre-2024" not in prompt
