# Master Prompt — Ignite R&D Grant Application Tool

> **For Claude Code.** This is the full context for a job interview technical assessment. Read this entire document before starting. Decide the architecture yourself — you have full autonomy over stack, structure, and approach. Optimise for the assessment criteria, not for what's most fun to build.

---

## What this is

A **technical assessment for a Forward Deployed Engineer role at SilverTree Equity** (a London-based software-focused private equity firm). The candidate has already passed two interviews. This is the build round. Submission deadline: **Friday 1 May, 11:59pm**.

The candidate will deliver:
1. The working tool (hosted or with local setup instructions)
2. A 10-15 minute video walkthrough (the candidate records this — you don't generate it)
3. A short paragraph (written before the build) on what they'd do with a full week instead of 3 days

You are building piece 1. Build it well enough that piece 2 has substance to walk through.

## What is being assessed

The brief is explicit about what graders care about. **Internalise this — every architecture decision should serve at least one of these:**

| Criterion | What good looks like |
|---|---|
| **Decisions** | The candidate can explain why they built it this way. Considered alternatives, made conscious choices. |
| **Usefulness** | The output actually helps a grant-writing consultant day-to-day. |
| **Working product** | It runs. It does what the candidate says it does. Graders can test it. |
| **Communication** | The candidate can walk a non-technical person through what it does and why it matters. |

Notice what is NOT on the list: code elegance, framework sophistication, exhaustive feature coverage, scalability. **A clean, working tool with thoughtful trade-offs beats an ambitious half-broken one.**

## The business problem

**Ignite Group** is a German R&D tax credit consultancy. Companies pay them to write applications for the **Forschungszulagengesetz (FZlG)** — a German federal R&D tax credit programme.

Key facts about FZlG you must encode correctly:
- **Credit rate:** 25% of qualifying R&D costs. **35% for SMEs** (defined as <€35M annual revenue).
- **Annual cap:** €3.5M per year per claimant for SMEs.
- **Eligible costs:**
  - Personnel costs (R&D staff salaries) — 100% eligible
  - Contractors — only **60% of contractor cost** is eligible
  - Capital expenditure — eligible **only since 2024**
- **Two-step process:**
  1. Apply to **BSFZ** (Bescheinigungsstelle Forschungszulage) for certification that the project qualifies as R&D
  2. Take certification to the **Finanzamt** (tax office) and file for the credit
- **Retroactive claims:** FZlG allows claims going back **up to 4 years**
- **The hard part:** Convincing the BSFZ that the project involves *genuine technical uncertainty* and a *systematic R&D approach* — not just normal product development. This is the critical narrative the BSFZ actually evaluates.

**The current pain:** When a new client enquiry comes in, an Ignite consultant gathers information by hand and writes the BSFZ application from scratch. Slow. Senior people doing junior work. The tool you're building automates the first draft so consultants only review and refine.

## What the tool must do

### Input — a form that collects:
1. Company name and what they do
2. R&D project description in plain language: what problem are they solving, what makes it technically uncertain, what's new
3. Team size and approximate % of time spent on R&D
4. Annual R&D spend, broken down: personnel, contractors, equipment/capital
5. Claim year — current year or which retroactive year (up to 4 back)

### Output — a structured draft application containing:
1. **Project title and summary**
2. **Statement of technical uncertainty** — the core narrative. Specific, convincing, BSFZ-grade. This is what they actually evaluate.
3. **Qualifying R&D activities** — mapped to the project description
4. **Estimated eligible costs and indicative tax credit** at 25% or 35% (auto-detect SME status from revenue if collected, else default to non-SME and flag for review)
5. **Notes for the consultant** — anything ambiguous, anything to verify, anything that strengthens or weakens the application before submission

The consultant reviews, edits, and submits. The tool does not file anything itself.

## Critical architecture decision: hybrid generation

**This is the single most important judgement call in the build.** The brief explicitly says "use an LLM, or build a structured template — either works." This is bait. The thoughtful answer is **both**:

- **Deterministic / template-based** for sections where hallucination is unacceptable:
  - Eligible cost calculations (this is arithmetic — never let an LLM do arithmetic)
  - Tax credit math (25% vs 35%)
  - SME eligibility flag
  - Any numerical figure the consultant or BSFZ will check
- **LLM-generated** for sections where prose quality matters:
  - Project title and summary
  - **Statement of technical uncertainty** (most important — spend the most prompt-engineering effort here)
  - Qualifying R&D activities narrative
  - Notes for the consultant (LLM identifies weaknesses in its own output)

Build a clean separation between these two paths. The candidate will explain this trade-off in the walkthrough as a key architectural decision: *"You don't let AI do maths, you do let it write prose. The thing graders penalise is hallucinated numbers in a regulatory document."*

## Stack guidance (you decide, but here's the thinking)

You have full autonomy. Optimise for: speed of build, ease of demo, clarity of code for the walkthrough.

Sensible defaults if you have no strong preference:
- **Backend:** Python with FastAPI or Flask. Python because the candidate is Python-fluent (per CV) and the LLM ecosystem is Python-first.
- **Frontend:** Streamlit if you want zero frontend work and a clean demo UI. Or simple HTML/JS served by FastAPI if you want more control. The form is 5 fields — don't over-engineer.
- **LLM:** Anthropic Claude (claude-sonnet-4 or claude-haiku-4-5 if cost matters). The brief says free-tier OpenAI or Anthropic is fine. Use Anthropic — the candidate is interviewing at a firm that uses Claude Code and the Amplify team uses Claude. Demonstrating Claude API fluency is a small but free signal.
- **Document output:** Generate the draft as Markdown rendered in the UI, with a "Download as .docx" button using `python-docx`. A consultant who can leave with a Word doc to edit is more useful than one who has to copy-paste from a webpage.
- **Persistence:** Skip databases. This is a prototype. In-memory or SQLite if you want to demonstrate a job queue stretch goal.

**Avoid these traps:**
- Don't build a full SPA in React. Time sink. Streamlit or simple HTML wins.
- Don't set up Docker, CI, deployment pipelines. Local with `pip install` instructions is fine. Hosted is better only if it's trivial (Streamlit Cloud, Replit) — don't burn 4 hours on infra.
- Don't build authentication. It's a prototype.
- Don't pretend to integrate with the actual BSFZ. There's no public API. The tool produces a draft document — that's the deliverable.

## Stretch goals — pick ONE, do it well

The brief lists six stretch goals. Picking too many = thin coverage = looks scattered. Pick one:

**Recommended: FZlG eligibility checker.** Before generating the draft, run a rule-based check:
- Is the company registered in Germany?
- Does the project description contain markers of genuine R&D vs. normal product work? (Use a small LLM call to classify on a 1-5 scale with reasoning shown.)
- Are the cost figures within FZlG limits (€3.5M cap)?
- Is the claim year within the 4-year retroactive window?

Display results as: **Eligible / Needs Review / Likely Ineligible** with reasoning. This adds real product value AND demonstrates rule-based + LLM hybrid judgement, which complements the main build's hybrid theme.

**Acceptable alternative:** Confidence scoring on each draft section (strong / needs review / weak) with reasoning. Cheap to build, demonstrates self-aware AI output.

**Skip these:**
- WBSO comparison (Dutch grants) — scope creep, no value to graders
- Consultant queue UI — looks impressive, costs hours, doesn't demonstrate AI judgement
- Document download — actually do this anyway, it's table stakes not stretch

## The technical uncertainty prompt — spend real effort here

The "Statement of Technical Uncertainty" is the section the BSFZ actually reads to decide. It's also the section where bad LLM output most clearly looks like bad LLM output. Spend disproportionate effort on this prompt.

Requirements for the prompt:
- Force the LLM to identify the **specific failure mode** in existing approaches the project is trying to overcome
- Force it to articulate **what the team does not know at the project's outset** (this is the definition of technical uncertainty under FZlG)
- Force it to distinguish **R&D from product engineering** — if the description sounds like product engineering, the prompt should flag this and ask the user to clarify
- Output should be 150-300 words, structured prose, no bullet points (BSFZ applications are written prose, not slides)

Test it with three deliberately varied inputs:
1. **Clear R&D:** A novel ML training approach, a new physical process, a fundamentally new algorithm
2. **Borderline:** A complex system integration with significant unknowns but using mostly known components
3. **Not R&D:** Building a CRUD app for a new market, customising existing software for a client

The system should handle all three differently. Case 3 should trigger a "this may not qualify as R&D under FZlG — please review" note, not just generate a confident-sounding application for non-R&D work.

## Things to include in the build that score easy points

The brief explicitly asks for these in the walkthrough — make sure the build supports them:

1. **"One thing you tried that didn't work."** Build something where you can demonstrate iteration. Suggested: First implement the technical uncertainty section as a single big prompt. Then split it into sub-prompts (failure mode → uncertainty → systematic approach). The split version produces noticeably better output. Keep both versions in the codebase as `v1_monolithic.py` and `v2_decomposed.py` so the candidate can show the difference in the walkthrough.

2. **"What you'd change with more time."** Don't build, but make sure architecture decisions leave room for: a feedback loop where rejected applications inform prompt refinement, retrieval over a corpus of past successful applications (RAG-lite), per-section confidence scoring, multi-language support (German output), reviewer dashboard.

3. **"Three improvements to the assessment."** This isn't part of the build — but the candidate will deliver it. Don't generate this. Leave it for them.

## Repo structure (suggested — adjust if you have a better idea)

```
ignite-grant-tool/
├── README.md                    # Setup, run instructions, architecture summary
├── ARCHITECTURE.md              # The "why" behind every major decision
├── pyproject.toml or requirements.txt
├── .env.example                 # ANTHROPIC_API_KEY=
├── app.py                       # Main entry point (Streamlit or FastAPI)
├── src/
│   ├── form_schema.py           # Pydantic models for input validation
│   ├── eligibility.py           # Rule-based eligibility checker (stretch goal)
│   ├── calculations.py          # Deterministic cost & credit math
│   ├── prompts/
│   │   ├── project_summary.py
│   │   ├── technical_uncertainty.py    # The most important prompt
│   │   ├── qualifying_activities.py
│   │   └── consultant_notes.py
│   ├── generator.py             # Orchestrates LLM calls + template assembly
│   ├── document_export.py       # python-docx output
│   └── llm_client.py            # Anthropic API wrapper
├── tests/
│   ├── test_eligibility.py
│   ├── test_calculations.py
│   └── fixtures/
│       ├── clear_rd_input.json
│       ├── borderline_rd_input.json
│       └── not_rd_input.json
└── examples/
    └── sample_outputs/          # Pre-generated outputs for the walkthrough demo
```

## Build sequence (suggested order)

Do them in this order so the candidate has something demoable at every checkpoint:

1. **Schema + form** (1 hr) — Pydantic input model, Streamlit form, no generation yet. Validates inputs.
2. **Calculations module** (1 hr) — Deterministic math: SME detection, eligible costs, tax credit. Unit tested. This is the "never let LLM do arithmetic" piece.
3. **One LLM prompt end-to-end** (2 hrs) — Wire up the project summary section. Get the API call working, error handling, basic prompt. Prove the loop.
4. **Technical uncertainty prompt** (3 hrs — spend the time here) — Iterate on this prompt with the three test cases. This is where the build wins or loses.
5. **Remaining sections** (2 hrs) — Qualifying activities and consultant notes. Cheaper to build now that pattern is set.
6. **Document assembly + .docx export** (1 hr) — Combine deterministic + LLM sections into one document. Download button.
7. **Eligibility checker stretch goal** (2 hrs) — Rules + LLM classification. Display verdict before main draft is generated.
8. **Polish + README + ARCHITECTURE.md** (2 hrs) — Setup instructions, decision log, sample outputs.

Total: ~14 hours. The brief says 4-8. Plan for 14. Build the README and ARCHITECTURE.md as you go, not at the end.

## What ARCHITECTURE.md must contain

This document is the candidate's evidence of "Decisions" (the top assessment criterion). It is read carefully. Sections to include:

1. **Hybrid generation rationale** — why deterministic for math, LLM for prose. Concrete: "I never want to be the engineer who shipped a tool that hallucinated a €312,000 credit number."
2. **Why decompose the technical uncertainty prompt** — show v1 vs v2 outputs side by side.
3. **Why Claude over GPT-4** — Anthropic's API was easier to get working with structured outputs, candidate is interviewing at a firm that uses Claude. (If you actually used GPT, justify that instead — but Claude is the right pick here.)
4. **Why no database / no auth** — prototype scope, real Ignite would need a queue and consultant accounts; out of scope.
5. **Why this stretch goal and not the others** — eligibility check pairs with the hybrid theme; queue and review UI are UX work that doesn't demonstrate AI judgement.
6. **Production gaps** — explicit list of what's missing for production: a feedback loop, a corpus of past successful applications for RAG, German-language output, reviewer roles, audit trails, BSFZ submission integration (if a public API existed), monitoring on prompt drift, eval set for prompt regressions.
7. **Cost model** — back-of-envelope: ~5,000 tokens input + 2,000 tokens output per draft × Claude Sonnet pricing = ~$X per draft. At Ignite's scale (estimate the consultant volume) = ~$Y/month. Compare to consultant hours saved.

## What README.md must contain

Different audience — an engineer who needs to run this in five minutes:

1. **What it does** in two sentences
2. **Setup** — one block of bash commands
3. **Environment** — `.env.example` reference, where to get an Anthropic key
4. **Run** — one command
5. **Try it** — a sample input the user can paste in to see it work
6. **Where to look in the code** — pointers to `src/prompts/` and `src/calculations.py` as the two interesting files

## Tone for all generated prose (LLM outputs)

The BSFZ is a German federal evaluator. Output prose should be:
- **Formal, precise, declarative** — not marketing language
- **Specific** — name the technologies, name the failure modes, name the unknowns
- **Honest about uncertainty** — "the team cannot predict at the outset whether..." is good. "Our innovative AI-powered solution will revolutionise..." is grounds for rejection.
- **English by default** — real applications would need German, but the brief doesn't require it. Note this as a production gap in ARCHITECTURE.md.

Write a system prompt that enforces this tone across all LLM calls.

## What you do NOT need to do

- Don't generate the candidate's video walkthrough script. They'll write that themselves.
- Don't generate the "what I'd do with a week" paragraph. They'll write that.
- Don't generate the "three improvements to the assessment" answer. They'll write that.
- Don't pretend to have access to real Ignite data, real BSFZ submissions, or real client information. Use realistic synthetic test cases.
- Don't try to make the tool legally accurate as a tax advisor. It's a drafting assistant for consultants, not a substitute for one. Make sure the consultant notes always reinforce this.

## Definition of done

The candidate should be able to:
1. `git clone`, `pip install`, set their `ANTHROPIC_API_KEY`, run one command, get a working UI
2. Type in a sample R&D project, hit submit, get a structured draft within 30 seconds
3. Download the draft as a `.docx`
4. Open `ARCHITECTURE.md` and walk through five clearly-articulated design decisions
5. Demonstrate the eligibility checker on a clearly-not-R&D input and show the system flagging it
6. Show the v1 vs v2 prompt difference for the technical uncertainty section as the "thing that didn't work first time"

Build for those six things. Anything else is gold-plating.

---

## Final note on judgement

The candidate's previous interviews showed Romil (the interviewer) values:
- **Specificity** — naming the metric, naming the trade-off, naming the risk
- **Bias to action over theorising** — ship the thing, then explain why
- **Self-awareness** — flagging weaknesses in your own work before someone else does
- **Operator thinking** — understanding what the user (the consultant) actually needs, not what's technically interesting

Every line of code, every prompt, every paragraph in the docs should reflect those values. If something feels like cleverness for its own sake, cut it. If something feels obvious but useful, keep it.

Build the thing. Write the docs as you go. Be ready to defend every decision.
