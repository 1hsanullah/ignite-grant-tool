# Project: Ignite R&D Grant Application Tool

This project is a technical assessment for a SilverTree Equity Forward Deployed Engineer role. Submission deadline: Friday 1 May, 11:59pm.

## Authoritative context

**Always read `Master_Prompt.md` at the start of every session.** That document is the master spec — business context, FZlG rules, architecture guidance, build sequence, definition of done. Do not improvise on anything covered there.

**Always read `TASK.md` at the start of every session.** That's the living state of the build — what's done, what's in progress, decisions made, things deferred. Update it after every meaningful change.

## Working principles

- Build for the four assessment criteria: Decisions, Usefulness, Working Product, Communication. Nothing else.
- Hybrid generation: deterministic for math, LLM for prose. Never let an LLM do arithmetic.
- Run code after writing it. Verify it works before claiming it's done.
- Push back if I ask for something that contradicts `Master_Prompt.md` — flag the conflict, don't silently comply.
- When making non-obvious decisions, explain the reasoning in `ARCHITECTURE.md` as we go (not at the end).
- Commit to git after each working phase.

## Stack

Decided in Plan Mode at the start of phase 1. Once chosen, stick to it. Do not rewrite in a different framework mid-build.

## Out of scope

Authentication, databases, deployment infrastructure, real BSFZ integration, German-language output, multi-tenant features. Note these in `ARCHITECTURE.md` as production gaps.