# Build State

**Last updated:** 2026-04-30 (Phase 8 complete — build complete)

## Done

### Phase 1 — Scaffold + form + schema
- `git init`, `.gitignore`, `requirements.txt`, `.env.example`
- `src/form_schema.py` — `GrantApplicationInput` Pydantic model with field validation and `is_sme` / `total_claimed_cost` properties
- `app.py` — Streamlit form: 5 fields across Company / R&D Project / Financials / Claim year sections; submit echoes validated Pydantic dict
- `README.md` stub with sample input for the walkthrough demo
- `ARCHITECTURE.md` — decisions 1–3 written (stack, hybrid generation, why Claude); stubs for decisions 4–7

### Phase 2 — Calculations module
- `src/calculations.py` — `CostCalculation` dataclass + `calculate()` function
  - SME flag (strict `<` €35M threshold), 60% contractor rule, capex eligibility from 2024, €3.5M annual cap
  - `indicative_credit` = `total_eligible × credit_rate` (never LLM)
- `tests/test_calculations.py` — 17 unit tests covering all boundary cases; 17/17 pass
- `pytest.ini` — sets rootdir and pythonpath for test discovery
- `app.py` updated — Phase 2 results (cost breakdown table, credit metrics, warnings) now render on submit

### Phase 3 — First end-to-end LLM call
- `src/llm_client.py` — `LLMClient` (Anthropic SDK wrapper), `LLMCallError`, shared system prompt with `cache_control: ephemeral`
  - Model constants: `SONNET_MODEL = "claude-sonnet-4-6"` (default, ~$0.003/draft), `OPUS_MODEL = "claude-opus-4-7"` (documented tunable lever for Phase 4)
  - System prompt (~700 tokens): BSFZ tone rules, FZlG programme context, evaluation criteria, borderline-project handling; annotated for caching (sub-threshold now — grows into Sonnet's 2048-token minimum in Phase 4–5)
  - `complete(user_prompt, *, model, max_tokens)` — one `messages.create` call; raises `LLMCallError` on API failure, `RuntimeError` if key missing
- `src/prompts/__init__.py` — package marker
- `src/prompts/project_summary.py` — `build_prompt()` + `generate()`; max_tokens=600; title on line 1 + 2–3 BSFZ-grade paragraphs
- `src/generator.py` — `GeneratedDraft` dataclass + `generate_draft(application, calc, llm)`; takes `calc` now so Phase 5 consultant-notes section doesn't require a signature change
- `app.py` updated — `_get_llm()` singleton via `@st.cache_resource`; spinner + `generate_draft` call; `st.markdown(draft.project_summary)` on success; clean `st.error` on `LLMCallError`
- `pytest` — 17/17 passing (no regressions)

### Phase 4 — Technical Uncertainty prompt
- `src/prompts/technical_uncertainty/` subpackage:
  - `v1_monolithic.py` — single-call version; `build_prompt()` + `generate()`
  - `v2_decomposed.py` — 3-stage version: failure mode → unknowns → synthesis; `V2Result` dataclass + stage builders + `generate()`
  - `__init__.py` — dispatch `generate(application, llm, *, version="v2") -> str`
- `tests/fixtures/` — `clear_rd_input.json`, `borderline_rd_input.json`, `not_rd_input.json`
- `tests/test_technical_uncertainty.py` — 11 new tests (prompt-builder strings + fixture loading); 28/28 pass
- `scripts/compare_uncertainty_prompts.py` — offline eval: runs all 3 fixtures × both versions; writes 6 markdown files to `examples/sample_outputs/`; prints summary table
- `src/generator.py` — added `technical_uncertainty: str` field to `GeneratedDraft`; added `uncertainty_version` kwarg to `generate_draft()`
- `app.py` — renders "Statement of technical uncertainty" section; "🔬 Compare v1 vs v2" checkbox inside form triggers side-by-side `st.tabs` view showing both versions

### Phase 8 — README polish, ARCHITECTURE.md completion
- `README.md` — rewrote: removed "Under construction", corrected env var to `OPENROUTER_API_KEY`, updated "five-field" description, fixed `prompts/technical_uncertainty.py` path (subpackage), added eligibility and docx mentions, added Tests section, updated "Where to look" table with `eligibility.py` and `document_export.py`
- `ARCHITECTURE.md` — updated Section 7 (eligibility) to describe what was built (4 checks, Haiku, graceful degradation); added Section 8 (document export design: hand-rolled markdown, conditional eligibility); renumbered old Section 8 (production gaps) → Section 9
- `TASK.md` — updated section reference (section 7 → section 9 for production gaps)

### Phase 7 — FZlG eligibility checker (stretch goal)
- `src/eligibility.py` — `Verdict` enum, `Check` / `EligibilityResult` dataclasses, `evaluate()` orchestrator
  - 4 checks: Germany registration (rule, new `Optional[bool]` field), cost cap (rule, reuses `calc.is_capped`), claim year (rule, always passes by schema construction), R&D classifier (LLM)
  - Verdict aggregation: any fail → Likely Ineligible; any warn → Needs Review; all pass → Eligible
- `src/prompts/rd_classifier.py` — 1–5 R&D score prompt using `HAIKU_MODEL`; `_parse_score_and_reasoning()` with regex + fallback to (3, raw) on malformed output; `LLMCallError` degrades to (3, "unavailable") — never crashes
- `src/llm_client.py` — added `HAIKU_MODEL = "anthropic/claude-haiku-4-5"` constant
- `src/form_schema.py` — added `is_germany_registered: Optional[bool] = None` field
- `app.py` — Germany radio (Yes/No/Not sure) in form; eligibility spinner + `st.success`/`st.warning`/`st.error` verdict block; `st.expander("Eligibility detail")` auto-expanded for non-Eligible verdicts; duplicate LLM init removed
- `src/document_export.py` — `build_docx(..., eligibility=None)` — renders "Eligibility assessment" section when supplied; backward-compatible default
- `tests/test_eligibility.py` — 23 unit tests (all using StubLLM / FailingLLM, no live API calls)
- `tests/test_document_export.py` — 2 new docx tests; 81/81 total passing

### Phase 6 — Document assembly + .docx export
- `src/document_export.py` — `build_docx(application, calc, draft) -> bytes`
  - Mirrors on-screen section order: title, cost metrics, cost breakdown table, warnings (suppressed when no flags), project summary, technical uncertainty, qualifying activities, consultant notes, disclaimer
  - Private `_render_markdown()` helper: handles bullets, numbered lists, blank-line paragraphs, `**bold**` runs — no external markdown lib
  - Cost breakdown uses a header row + 5 data rows; "Total eligible" rows bolded
  - Warnings section only emitted when at least one flag fires (`revenue_unknown`, `capex_excluded`, `is_capped`)
- `tests/test_document_export.py` — 6 unit tests; 56/56 total passing
- `app.py` — `st.download_button` added after consultant notes; file named `FZlG_application_{company}_{year}.docx`

### Phase 5 — Qualifying activities + consultant notes
- `src/prompts/qualifying_activities.py` — numbered-list prompt mapping project description to FZlG activity categories (Experimental development / Applied research / Fundamental research); takes `calc` for cost context
- `src/prompts/consultant_notes.py` — two-layer hybrid: `deterministic_notes()` fires factual flags from `calc` (revenue unknown, capex excluded, cap hit, contractors present); `build_prompt()` chains the three generated sections back to the LLM for self-critique ([Verify] / [Weakness] / [Strengthen] bullets)
- `src/generator.py` — `GeneratedDraft` expanded with `qualifying_activities` + `consultant_notes`; `generate_draft()` now orchestrates 6 LLM calls total
- `app.py` — renders two new sections; spinner copy updated; deterministic-first ordering noted in caption
- `tests/test_qualifying_activities.py` + `tests/test_consultant_notes.py` — 22 new unit tests; 50/50 passing

## In Progress

*(nothing — build complete)*

## Next up

*(all phases complete — see Definition of Done in Master_Prompt.md)*
- Phase 8: README polish, ARCHITECTURE.md completion, sample outputs

## Decisions made

- **Stack:** Streamlit + Python 3.11 + Pydantic v2 + Anthropic Sonnet 4.6 + python-docx. No database, no auth.
- **Hybrid generation:** `calculations.py` for all math (never LLM), `src/prompts/` for all prose.
- **Stretch goal:** FZlG eligibility checker (rule-based + LLM classification, pre-generation gate).
- **Model:** Sonnet 4.6 default. Opus 4.7 as a documented tunable lever for the Technical Uncertainty prompt only.
- **API gateway:** OpenRouter (`https://openrouter.ai/api/v1`) via the `openai` SDK. Same Claude models, OpenRouter handles billing. Model IDs prefixed `anthropic/` (e.g. `anthropic/claude-sonnet-4-6`).

## Deferred / production gaps

Documented in `ARCHITECTURE.md` section 9: German output, feedback loop, RAG, reviewer dashboard, audit trail, BSFZ submission integration, prompt drift monitoring, multi-tenant isolation.

## Open questions

- Hosting: local-only or Streamlit Community Cloud? (Decide in Phase 8)
- Model budget: Sonnet 4.6 default confirmed — Opus 4.7 toggle only if Sonnet output is weak in Phase 4 testing
