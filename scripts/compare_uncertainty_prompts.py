#!/usr/bin/env python
"""
Run all three test fixtures through both v1 (monolithic) and v2 (decomposed)
technical-uncertainty prompts and write labelled markdown to examples/sample_outputs/.

Usage:
    python scripts/compare_uncertainty_prompts.py

Requires OPENROUTER_API_KEY in .env.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

# Allow running from the project root without installing the package.
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

from src.form_schema import GrantApplicationInput
from src.llm_client import LLMCallError, LLMClient
from src.prompts.technical_uncertainty import v1_monolithic, v2_decomposed

FIXTURES_DIR = Path("tests/fixtures")
OUTPUT_DIR = Path("examples/sample_outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FIXTURE_NAMES = [
    "clear_rd_input",
    "borderline_rd_input",
    "not_rd_input",
]


def word_count(text: str) -> int:
    return len(text.split())


def has_warning(text: str) -> bool:
    return "⚠" in text or "may not qualify" in text.lower()


def run_all() -> None:
    llm = LLMClient()
    results: list[dict] = []

    for name in FIXTURE_NAMES:
        path = FIXTURES_DIR / f"{name}.json"
        application = GrantApplicationInput.model_validate(
            json.loads(path.read_text(encoding="utf-8"))
        )
        print(f"\n{'=' * 60}")
        print(f"Fixture : {name}")
        print(f"Company : {application.company_name}")

        # ── v1 monolithic ──────────────────────────────────────────────────
        print("  Running v1 (monolithic)…", end=" ", flush=True)
        t0 = time.perf_counter()
        try:
            v1_text = v1_monolithic.generate(application, llm)
        except LLMCallError as exc:
            v1_text = f"ERROR: {exc}"
        v1_elapsed = time.perf_counter() - t0
        print(f"{v1_elapsed:.1f}s")

        # ── v2 decomposed ──────────────────────────────────────────────────
        print("  Running v2 (decomposed)…", end=" ", flush=True)
        t0 = time.perf_counter()
        try:
            v2_result = v2_decomposed.generate(application, llm)
            v2_text = v2_result.synthesis
        except LLMCallError as exc:
            v2_result = None
            v2_text = f"ERROR: {exc}"
        v2_elapsed = time.perf_counter() - t0
        print(f"{v2_elapsed:.1f}s")

        # ── Write v1 output ────────────────────────────────────────────────
        v1_path = OUTPUT_DIR / f"{name}_v1_monolithic.md"
        v1_path.write_text(
            f"# {name} — v1 monolithic\n\n"
            f"**Latency:** {v1_elapsed:.1f}s  \n"
            f"**Word count:** {word_count(v1_text)}  \n"
            f"**Warning flag:** {'Yes' if has_warning(v1_text) else 'No'}\n\n"
            f"---\n\n{v1_text}\n",
            encoding="utf-8",
        )

        # ── Write v2 output (with intermediate stages) ─────────────────────
        stages_md = ""
        if v2_result is not None:
            stages_md = (
                f"### Stage 1 — Failure mode\n\n{v2_result.failure_mode}\n\n"
                f"### Stage 2 — Unknowns at outset\n\n{v2_result.unknowns}\n\n"
                f"### Stage 3 — Synthesis\n\n"
            )
        v2_path = OUTPUT_DIR / f"{name}_v2_decomposed.md"
        v2_path.write_text(
            f"# {name} — v2 decomposed\n\n"
            f"**Latency:** {v2_elapsed:.1f}s  \n"
            f"**Word count:** {word_count(v2_text)}  \n"
            f"**Warning flag:** {'Yes' if has_warning(v2_text) else 'No'}\n\n"
            f"---\n\n{stages_md}{v2_text}\n",
            encoding="utf-8",
        )

        results.append(
            {
                "fixture": name,
                "v1_words": word_count(v1_text),
                "v1_elapsed": f"{v1_elapsed:.1f}s",
                "v1_warning": has_warning(v1_text),
                "v2_words": word_count(v2_text),
                "v2_elapsed": f"{v2_elapsed:.1f}s",
                "v2_warning": has_warning(v2_text),
            }
        )

    # ── Summary table ──────────────────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(
        f"{'Fixture':<25} {'V1 wds':>6} {'V1 t':>6} {'V1⚠':>4}  "
        f"{'V2 wds':>6} {'V2 t':>6} {'V2⚠':>4}"
    )
    print("-" * 65)
    for r in results:
        print(
            f"{r['fixture']:<25} {r['v1_words']:>6} {r['v1_elapsed']:>6} "
            f"{'Y' if r['v1_warning'] else 'N':>4}  "
            f"{r['v2_words']:>6} {r['v2_elapsed']:>6} "
            f"{'Y' if r['v2_warning'] else 'N':>4}"
        )
    print(f"\nOutputs written to {OUTPUT_DIR}/")


if __name__ == "__main__":
    run_all()
