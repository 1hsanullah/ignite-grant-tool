# Build State

**Last updated:** 2026-04-30 (Phase 3 complete)

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

## In Progress

*(nothing — starting Phase 4)*

## Next up

- **Phase 4: Technical Uncertainty prompt** v1 (monolithic) + v2 (decomposed), three test fixtures
- Phase 4: Technical Uncertainty prompt v1 (monolithic) + v2 (decomposed), three test fixtures
- Phase 5: Qualifying activities + consultant notes sections
- Phase 6: Document assembly + .docx export
- Phase 7: FZlG eligibility checker (stretch)
- Phase 8: README polish, ARCHITECTURE.md completion, sample outputs

## Decisions made

- **Stack:** Streamlit + Python 3.11 + Pydantic v2 + Anthropic Sonnet 4.6 + python-docx. No database, no auth.
- **Hybrid generation:** `calculations.py` for all math (never LLM), `src/prompts/` for all prose.
- **Stretch goal:** FZlG eligibility checker (rule-based + LLM classification, pre-generation gate).
- **Model:** Sonnet 4.6 default. Opus 4.7 as a documented tunable lever for the Technical Uncertainty prompt only.
- **API gateway:** OpenRouter (`https://openrouter.ai/api/v1`) via the `openai` SDK. Same Claude models, OpenRouter handles billing. Model IDs prefixed `anthropic/` (e.g. `anthropic/claude-sonnet-4-6`).

## Deferred / production gaps

Documented in `ARCHITECTURE.md` section 7: German output, feedback loop, RAG, reviewer dashboard, audit trail, BSFZ submission integration, prompt drift monitoring, multi-tenant isolation.

## Open questions

- Hosting: local-only or Streamlit Community Cloud? (Decide in Phase 8)
- Model budget: Sonnet 4.6 default confirmed — Opus 4.7 toggle only if Sonnet output is weak in Phase 4 testing
