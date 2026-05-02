# Ignite R&D Grant Application Tool

A drafting assistant for **FZlG** (Forschungszulagengesetz) R&D tax credit applications. A consultant fills in a form describing the company and its R&D project; the tool runs an eligibility pre-check, generates a structured BSFZ-ready draft with deterministic cost calculations and LLM-authored prose, and delivers a downloadable `.docx` — in under 45 seconds.

---

## Live demo

**[https://ignite-grant-tool-nmska4bk2vyqfgrzgjxt66.streamlit.app](https://ignite-grant-tool-nmska4bk2vyqfgrzgjxt66.streamlit.app)**

No setup required — open the link and use it directly.

## Local setup (optional)

```bash
git clone https://github.com/1hsanullah/ignite-grant-tool
cd ignite-grant-tool
pip install -r requirements.txt
cp .env.example .env          # add your OpenRouter API key
streamlit run app.py
```

## Tests

The deterministic logic (FZlG calculations, eligibility rules, prompt builders, document assembly) is fully unit-tested — no API key required:

```bash
pytest
```

81 tests, all passing. Run these before the LLM-dependent path to verify the math is correct.

## Try it

Paste this into the form to see a complete generated draft:

```
Company name:          Tensorwave GmbH
What they do:          Deep learning infrastructure for autonomous vehicle perception
R&D project:           Novel sparse attention mechanism for real-time LiDAR point-cloud
                       processing. Existing dense-attention approaches cannot maintain
                       sub-100ms inference latency under adversarial weather conditions.
                       The team does not know at the outset whether sparsity above 85%
                       can preserve detection accuracy at long range — this is the core
                       technical uncertainty. Work is structured as systematic ablation
                       studies varying sparsity thresholds, batch geometry, and weather
                       simulation parameters.
Team size:             8 engineers, 80% R&D time
Annual revenue:        €4,200,000 (SME — qualifies for the 35% credit rate)
Personnel costs:       €480,000
Contractor costs:      €60,000
Equipment / capex:     €30,000
Claim year:            2025
Germany registered:    Yes
```

Expected output: **Eligible** (green) verdict at the top → cost table (total eligible ~€522,000, indicative credit ~€182,700) → four LLM-generated prose sections → "Download as .docx" button.

## What gets generated

| Section | Source |
|---|---|
| FZlG eligibility verdict (Eligible / Needs Review / Likely Ineligible) | Rule-based + LLM classifier |
| Indicative cost calculation (SME status, credit rate, eligible totals) | Deterministic — never LLM |
| Project title and summary | LLM |
| Statement of technical uncertainty | LLM (v2 decomposed — 3 chained sub-prompts) |
| Qualifying R&D activities (numbered, classified by Frascati category) | LLM |
| Notes for the consultant ([Verify] / [Weakness] / [Strengthen] bullets) | Deterministic flags + LLM |
| .docx download | python-docx — mirrors on-screen content |

## Where to look in the code

| File | What it does |
|---|---|
| `src/calculations.py` | Deterministic FZlG math — SME flag, eligible costs, credit amount |
| `src/form_schema.py` | Pydantic input model — the contract between UI and generation |
| `src/eligibility.py` | Eligibility checker — 3 rule-based checks + LLM R&D classifier |
| `src/prompts/technical_uncertainty/v2_decomposed.py` | The highest-effort prompt — what BSFZ actually evaluates |
| `src/generator.py` | Orchestrates all LLM calls and assembles the draft |
| `src/document_export.py` | Assembles the .docx from deterministic data + generated prose |

## Architecture

See `ARCHITECTURE.md` for the reasoning behind every major design decision, including why the math is never delegated to an LLM and how the eligibility checker extends the same hybrid pattern.
