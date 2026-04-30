# Architecture Decision Log

> For each major decision: what was chosen, what was considered, and why.
> Updated during the build — not retrospectively at the end.

---

## 1. Stack choice

**Chosen:** Python 3.11 + Streamlit + Pydantic v2 + Anthropic Claude API + python-docx

**Considered and rejected:**

| Alternative | Why rejected |
|---|---|
| FastAPI + Jinja2 + custom HTML form | ~4–6 hours of UI plumbing (form HTML, CSS, error rendering, fetch handlers) for zero visible quality gain |
| FastAPI + React SPA | Master prompt explicitly flags this as a time sink. A 5-field form is not a React problem. |
| Gradio | ML-flavoured defaults; weaker for long structured text output and a download button |
| OpenAI GPT-4o | See decision 3 below |
| Poetry / pyproject.toml | `requirements.txt` is one fewer tool for a grader to know about; master prompt accepts either |

**Why Streamlit:** The deliverable is a 5-field form, a structured prose panel, and a download button. That is exactly what Streamlit was designed for. Choosing a heavier framework would mean spending time on plumbing instead of on the two things that actually determine quality: prompt engineering and the deterministic/LLM split.

---

## 2. Hybrid generation: deterministic math, LLM prose

**The single most important architectural decision.**

The output contains two fundamentally different categories of information:

**Category A — numbers:**
Eligible costs, indicative tax credit, SME flag. These will be reviewed by a consultant and may ultimately reach a German federal tax authority (Finanzamt). If they are wrong, the application fails — or worse, a client relies on them and files incorrectly. An LLM will sometimes hallucinate numbers, particularly when the prompt also requests prose. Never let an LLM do arithmetic.

**Category B — prose:**
Technical uncertainty narrative, qualifying activities description, consultant notes. These require contextual reasoning, nuanced language, and the ability to adapt a generic template to a specific project. Templates cannot produce this at quality. LLMs can.

**The implementation:** `src/calculations.py` contains all arithmetic with no LLM involvement — fully unit-tested. `src/prompts/` contains all prose prompts with no arithmetic. They are assembled by `src/generator.py`.

> Design heuristic: "I never want to be the engineer who shipped a tool that hallucinated a €312,000 credit number in a regulatory document."

---

## 3. Why Claude over GPT-4

**Chosen:** Anthropic Claude Sonnet 4.6 (`claude-sonnet-4-6`)

**Considered:** OpenAI GPT-4o, GPT-4o-mini

**Reasons:**

1. **Signal to the interviewer:** The candidate is interviewing at a firm that uses Claude Code. Demonstrating Anthropic API fluency is a small but free positive signal.

2. **Tone alignment:** Claude's default prose style — formal, declarative, specific — matches the BSFZ tone requirement better than GPT-4o's tendency toward slightly warmer language. Less post-processing needed.

3. **Cost:** Sonnet 4.6 at roughly $0.003 per draft is an order of magnitude cheaper than Opus 4.7 for comparable quality on this task.

4. **Tunable lever:** If Sonnet output on the Technical Uncertainty section proves weak in testing, swapping that specific call to Opus 4.7 is a one-line change in `src/llm_client.py` — documented there as a named constant.

---

## 4. Prompt caching strategy — system prompt as shared cache anchor

**Chosen:** A single shared system prompt (~700 tokens, growing to ~1500+ in Phases 4–5) annotated with `cache_control: {"type": "ephemeral"}` on every call. Per-section user prompts are short and unique per submission.

**Why this layout:**

Anthropic's prompt cache is a prefix match: the cached prefix must be byte-identical on every request. Rendering order is `tools → system → messages`. Anything that changes per request (user company name, project description, figures) sits in the `messages` array — after the cache breakpoint. The system prompt never changes within a session and rarely changes across sessions (only on prompt iterations), so it is the natural anchor.

**Sonnet 4.6 minimum cacheable prefix = 2048 tokens.** At Phase 3 launch the system prompt is ~700 tokens — below threshold. The cache_control annotation is harmless (silently ignored if below minimum) and means the cache will activate automatically as Phase 4–5 domain context brings the system prompt above threshold. No code change will be needed when that happens.

**Why not per-section caching:** Each section call sends a different user prompt. The system prompt is the only repeated block, so it is the only sensible cache point. Attempting to cache user-prompt prefixes would require contrived shared preambles across sections with no benefit.

---

## 5. Why decompose the technical uncertainty prompt (v1 vs v2)

*(To be written when Phase 4 is complete — will include side-by-side output comparison)*

---

## 6. Why no database / no auth

**No database:** This is a prototype. Each form submission is a stateless request-response cycle. A production system would need a job queue (LLM calls can take 10–15s), consultant accounts, and an audit trail of all generated drafts. These are explicitly out of scope. Noted as production gaps below.

**No auth:** Same reason. A production system serving multiple consultants at Ignite would need roles (consultant, reviewer, admin), SSO, and per-client data separation. None of that is needed to demonstrate the core value of the tool.

---

## 7. Why this stretch goal (eligibility checker) and not the others

**Chosen:** Pre-generation FZlG eligibility check — rule-based + LLM classification — displayed before the main draft.

**Rejected:**
- *WBSO comparison (Dutch grants):* Out of scope. No value to graders evaluating a German grant tool.
- *Consultant queue UI:* UX work that doesn't demonstrate AI judgement. Costs 4+ hours.
- *Confidence scoring per section:* Good fallback if eligibility checker runs over time. Less product value.

**Why eligibility checker:** It extends the hybrid-generation thesis directly — rules for the objective checks (4-year window, €3.5M cap, German company requirement), LLM classification for the subjective question ("is this genuine R&D or normal product development?"). It also adds real product value: a consultant knows within 30 seconds whether a new enquiry is worth pursuing.

---

## 8. Production gaps

Explicit list of what would need to be built before Ignite could use this in production:

| Gap | What's needed |
|---|---|
| German-language output | The BSFZ application is submitted in German. A translation layer or German-native prompts are required. |
| Feedback loop | Rejected applications should inform prompt refinement. Needs a structured feedback collection mechanism and an eval set. |
| RAG over past applications | A corpus of successful BSFZ submissions would dramatically improve relevance and specificity. Needs a vector store + retrieval layer. |
| Reviewer dashboard | Consultants need to review, annotate, and track drafts. Needs persistent storage, user accounts, and a structured review workflow. |
| Audit trail | Every generated draft and every edit should be logged. Regulatory context makes this non-optional in production. |
| BSFZ submission integration | No public API currently exists. If one becomes available, submission could be automated from the reviewed draft. |
| Prompt drift monitoring | As Claude models update, prompt outputs can shift. An eval harness running against known-good fixtures would catch regressions. |
| Per-client data separation | In a multi-tenant setup, strict data isolation between Ignite clients is required. |
| Cost model at scale | Back-of-envelope: ~5,000 tokens input + 2,000 tokens output per draft × Sonnet 4.6 pricing ≈ $0.003–0.005 per draft. At 50 drafts/month (estimate for a boutique consultancy): ~$0.15–0.25/month in API costs — negligible. At 500/month: ~$2.50. API cost is not the constraint; consultant review time is. |
