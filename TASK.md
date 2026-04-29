# Build State

**Last updated:** 2026-04-29 (Phase 2 complete)

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

## In Progress

*(nothing — starting Phase 3)*

## Next up

- **Phase 3: First end-to-end LLM call** (project summary via Anthropic API)
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

## Deferred / production gaps

Documented in `ARCHITECTURE.md` section 7: German output, feedback loop, RAG, reviewer dashboard, audit trail, BSFZ submission integration, prompt drift monitoring, multi-tenant isolation.

## Open questions

- Hosting: local-only or Streamlit Community Cloud? (Decide in Phase 8)
- Model budget: Sonnet 4.6 default confirmed — Opus 4.7 toggle only if Sonnet output is weak in Phase 4 testing
