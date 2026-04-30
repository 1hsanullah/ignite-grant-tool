from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.calculations import calculate
from src.eligibility import (
    Check,
    EligibilityResult,
    Verdict,
    _aggregate_verdict,
    _check_claim_year,
    _check_cost_cap,
    _check_germany,
    _check_rd_classification,
    evaluate,
)
from src.form_schema import GrantApplicationInput
from src.llm_client import LLMCallError
from src.prompts.rd_classifier import _parse_score_and_reasoning

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str, **overrides) -> GrantApplicationInput:
    data = json.loads((FIXTURES / name).read_text())
    data.update(overrides)
    return GrantApplicationInput(**data)


class StubLLM:
    def __init__(self, response: str = "Score: 5\nReasoning: Clear R&D."):
        self._response = response

    def complete(self, *args, **kwargs) -> str:
        return self._response


class FailingLLM:
    def complete(self, *args, **kwargs):
        raise LLMCallError("Simulated API failure")


# ── _parse_score_and_reasoning ────────────────────────────────────────────────

def test_parse_well_formed():
    score, reasoning = _parse_score_and_reasoning("Score: 4\nReasoning: Strong technical uncertainty evident.")
    assert score == 4
    assert "technical uncertainty" in reasoning


def test_parse_malformed_falls_back_to_3():
    score, reasoning = _parse_score_and_reasoning("I think it looks good.")
    assert score == 3
    assert "I think it looks good." in reasoning


def test_parse_score_5():
    score, _ = _parse_score_and_reasoning("Score: 5\nReasoning: Crystal clear R&D.")
    assert score == 5


def test_parse_score_1():
    score, _ = _parse_score_and_reasoning("Score: 1\nReasoning: Obvious product engineering.")
    assert score == 1


# ── individual rule-based checks ──────────────────────────────────────────────

def test_germany_registered_true_passes():
    app = _load("clear_rd_input.json", is_germany_registered=True)
    check = _check_germany(app)
    assert check.status == "pass"


def test_germany_registered_false_fails():
    app = _load("clear_rd_input.json", is_germany_registered=False)
    check = _check_germany(app)
    assert check.status == "fail"
    assert "Betriebsstätte" in check.reasoning


def test_germany_registered_none_warns():
    app = _load("clear_rd_input.json", is_germany_registered=None)
    check = _check_germany(app)
    assert check.status == "warn"


def test_cost_cap_passes_when_not_capped():
    app = _load("clear_rd_input.json")
    calc = calculate(app)
    assert not calc.is_capped
    check = _check_cost_cap(calc)
    assert check.status == "pass"


def test_cost_cap_warns_when_capped():
    app = _load("clear_rd_input.json", personnel_cost_eur=4_000_000.0)
    calc = calculate(app)
    assert calc.is_capped
    check = _check_cost_cap(calc)
    assert check.status == "warn"
    assert "3,500,000" in check.reasoning


def test_claim_year_always_passes():
    app = _load("clear_rd_input.json")
    check = _check_claim_year(app)
    assert check.status == "pass"


def test_rd_classification_pass_for_score_4():
    check = _check_rd_classification(4, "Strong indicators of systematic R&D.")
    assert check.status == "pass"


def test_rd_classification_pass_for_score_5():
    check = _check_rd_classification(5, "Clear R&D.")
    assert check.status == "pass"


def test_rd_classification_warn_for_score_3():
    check = _check_rd_classification(3, "Borderline.")
    assert check.status == "warn"


def test_rd_classification_fail_for_score_2():
    check = _check_rd_classification(2, "Looks like product engineering.")
    assert check.status == "fail"


def test_rd_classification_fail_for_score_1():
    check = _check_rd_classification(1, "Plain CRUD application.")
    assert check.status == "fail"


# ── _aggregate_verdict ────────────────────────────────────────────────────────

def test_all_pass_gives_eligible():
    checks = [
        Check("A", "pass", "ok"),
        Check("B", "pass", "ok"),
    ]
    assert _aggregate_verdict(checks) == Verdict.ELIGIBLE


def test_any_warn_gives_needs_review():
    checks = [
        Check("A", "pass", "ok"),
        Check("B", "warn", "borderline"),
    ]
    assert _aggregate_verdict(checks) == Verdict.NEEDS_REVIEW


def test_any_fail_gives_likely_ineligible():
    checks = [
        Check("A", "warn", "borderline"),
        Check("B", "fail", "bad"),
    ]
    assert _aggregate_verdict(checks) == Verdict.LIKELY_INELIGIBLE


# ── evaluate() integration ────────────────────────────────────────────────────

def test_evaluate_eligible_when_all_pass():
    app = _load("clear_rd_input.json", is_germany_registered=True)
    calc = calculate(app)
    result = evaluate(app, calc, StubLLM("Score: 5\nReasoning: Clear R&D."))
    assert result.verdict == Verdict.ELIGIBLE
    assert result.rd_score == 5
    assert len(result.checks) == 4


def test_evaluate_needs_review_for_score_3():
    app = _load("clear_rd_input.json", is_germany_registered=True)
    calc = calculate(app)
    result = evaluate(app, calc, StubLLM("Score: 3\nReasoning: Borderline."))
    assert result.verdict == Verdict.NEEDS_REVIEW


def test_evaluate_likely_ineligible_when_germany_false():
    app = _load("clear_rd_input.json", is_germany_registered=False)
    calc = calculate(app)
    result = evaluate(app, calc, StubLLM("Score: 5\nReasoning: Clear R&D."))
    assert result.verdict == Verdict.LIKELY_INELIGIBLE


def test_evaluate_likely_ineligible_for_low_rd_score():
    app = _load("clear_rd_input.json", is_germany_registered=True)
    calc = calculate(app)
    result = evaluate(app, calc, StubLLM("Score: 1\nReasoning: CRUD app."))
    assert result.verdict == Verdict.LIKELY_INELIGIBLE


def test_evaluate_degrades_gracefully_on_llm_failure():
    app = _load("clear_rd_input.json", is_germany_registered=True)
    calc = calculate(app)
    result = evaluate(app, calc, FailingLLM())
    # FailingLLM causes rd_classifier.generate to catch and return (3, fallback_msg)
    assert result.verdict == Verdict.NEEDS_REVIEW
    assert result.rd_score == 3
    assert "unavailable" in result.rd_reasoning.lower()
