from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.form_schema import GrantApplicationInput
from src.prompts.technical_uncertainty import v1_monolithic, v2_decomposed

FIXTURES_DIR = Path(__file__).parent / "fixtures"
FIXTURE_FILES = ["clear_rd_input.json", "borderline_rd_input.json", "not_rd_input.json"]


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


# ── v1 monolithic ──────────────────────────────────────────────────────────────

def test_v1_build_prompt_includes_project_description():
    app = _make_application(project_description="X" * 60)
    assert "X" * 60 in v1_monolithic.build_prompt(app)


def test_v1_build_prompt_includes_failure_mode_instruction():
    prompt = v1_monolithic.build_prompt(_make_application())
    assert "failure mode" in prompt.lower()


def test_v1_build_prompt_includes_unknowns_instruction():
    prompt = v1_monolithic.build_prompt(_make_application())
    assert "does not know" in prompt.lower() or "unknown" in prompt.lower()


def test_v1_build_prompt_includes_borderline_guard():
    prompt = v1_monolithic.build_prompt(_make_application())
    assert "may not qualify" in prompt.lower()


# ── v2 decomposed ─────────────────────────────────────────────────────────────

def test_v2_failure_mode_prompt_includes_project_description():
    app = _make_application(project_description="Y" * 60)
    assert "Y" * 60 in v2_decomposed.build_failure_mode_prompt(app)


def test_v2_unknowns_prompt_threads_failure_mode_text():
    app = _make_application()
    failure_mode = "Existing solvers fail under high sparsity conditions."
    prompt = v2_decomposed.build_unknowns_prompt(app, failure_mode)
    assert failure_mode in prompt


def test_v2_synthesis_prompt_threads_both_prior_stages():
    app = _make_application()
    failure_mode = "Existing methods diverge under load."
    unknowns = "It is unknown whether approach X will converge."
    prompt = v2_decomposed.build_synthesis_prompt(app, failure_mode, unknowns)
    assert failure_mode in prompt
    assert unknowns in prompt


def test_v2_synthesis_prompt_includes_borderline_guard():
    prompt = v2_decomposed.build_synthesis_prompt(_make_application(), "fm", "uk")
    assert "may not qualify" in prompt.lower()


# ── fixture loading ────────────────────────────────────────────────────────────

@pytest.mark.parametrize("filename", FIXTURE_FILES)
def test_fixtures_load_as_valid_inputs(filename):
    path = FIXTURES_DIR / filename
    data = json.loads(path.read_text(encoding="utf-8"))
    app = GrantApplicationInput.model_validate(data)
    assert len(app.project_description) >= 50
