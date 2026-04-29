# Ignite R&D Grant Application Tool

A drafting assistant for **FZlG** (Forschungszulagengesetz) R&D tax credit applications. A consultant fills in a five-field form describing the company and its R&D project; the tool generates a structured BSFZ-ready draft with deterministic cost calculations and LLM-authored prose — in under 30 seconds.

> **Status:** Under construction — see `TASK.md` for current phase.

---

## Setup

```bash
git clone <repo-url>
cd ignite-grant-tool
pip install -r requirements.txt
cp .env.example .env
# Paste your Anthropic API key into .env
```

Get an Anthropic API key at [console.anthropic.com](https://console.anthropic.com).

## Run

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

## Try it

Paste this into the form to see a complete generated draft:

```
Company: Tensorwave GmbH
What they do: Deep learning infrastructure for autonomous vehicle perception
Project: Novel sparse attention mechanism for real-time LiDAR point-cloud processing
         that reduces compute by 40% without sacrificing detection accuracy at long range.
         The team does not know at the outset whether sparsity can be maintained below
         100ms latency under adversarial weather conditions — this is the core uncertainty.
Team: 8 engineers, 80% R&D time
Revenue: €4.2M (SME)
Costs: Personnel €480,000 / Contractors €60,000 / Capex €30,000
Claim year: 2025
```

## Where to look in the code

| File | What it does |
|---|---|
| `src/form_schema.py` | Pydantic input model — the contract between UI and generation |
| `src/calculations.py` | Deterministic FZlG math — SME flag, eligible costs, credit amount |
| `src/prompts/technical_uncertainty.py` | The highest-effort prompt — what BSFZ actually evaluates |
| `src/generator.py` | Orchestrates LLM calls and assembles the final document |

## Architecture

See `ARCHITECTURE.md` for the reasoning behind every major design decision.
