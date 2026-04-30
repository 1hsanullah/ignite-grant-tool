from datetime import date

import streamlit as st
from pydantic import ValidationError

from src.calculations import calculate
from src.document_export import build_docx
from src.eligibility import EligibilityResult, Verdict, evaluate
from src.form_schema import GrantApplicationInput
from src.generator import generate_draft
from src.llm_client import LLMCallError, LLMClient
from src.prompts.technical_uncertainty import v1_monolithic, v2_decomposed


@st.cache_resource
def _get_llm() -> tuple[LLMClient | None, str | None]:
    """Initialise the Anthropic client once per process; return (client, error)."""
    try:
        return LLMClient(), None
    except RuntimeError as exc:
        return None, str(exc)


def render_form() -> None:
    st.set_page_config(
        page_title="Ignite | FZlG Grant Application",
        layout="centered",
    )
    st.title("Ignite R&D Grant Application")
    st.caption(
        "Generate a first-draft FZlG (Forschungszulagengesetz) application for BSFZ review. "
        "All outputs require consultant review before submission."
    )

    with st.form("application_form"):
        # ── Company ──────────────────────────────────────────────────────────
        st.subheader("Company")
        company_name = st.text_input(
            "Company name *",
            placeholder="e.g. Acme Technologies GmbH",
        )
        company_description = st.text_area(
            "What does the company do? *",
            placeholder="Briefly describe the company's business, sector, and main products or services.",
            height=80,
        )

        st.divider()

        # ── R&D Project ──────────────────────────────────────────────────────
        st.subheader("R&D Project")
        project_description = st.text_area(
            "Describe the R&D project *",
            placeholder=(
                "What problem are you solving?\n"
                "What makes the solution technically uncertain — what does the team not know at the outset?\n"
                "What is novel or systematic about the approach?\n"
                "What would a failed experiment look like?"
            ),
            height=220,
        )

        col1, col2 = st.columns(2)
        with col1:
            team_size = st.number_input("R&D team size *", min_value=1, step=1, value=5)
        with col2:
            rd_time_pct = st.slider("% of time on R&D *", min_value=1, max_value=100, value=70)

        st.divider()

        # ── Financials ───────────────────────────────────────────────────────
        st.subheader("Financials")

        knows_revenue = st.checkbox(
            "I know the company's annual revenue (used to determine SME status)"
        )
        annual_revenue_eur = None
        if knows_revenue:
            annual_revenue_eur = st.number_input(
                "Annual revenue (€)",
                min_value=0.0,
                step=500_000.0,
                help="SME threshold: <€35M qualifies for the 35% credit rate instead of 25%.",
            )

        col3, col4, col5 = st.columns(3)
        with col3:
            personnel_cost_eur = st.number_input(
                "Personnel costs (€) *",
                min_value=0.0,
                step=10_000.0,
                value=200_000.0,
            )
        with col4:
            contractor_cost_eur = st.number_input(
                "Contractor costs (€)",
                min_value=0.0,
                step=10_000.0,
                value=0.0,
                help="60% of contractor costs count as eligible under FZlG.",
            )
        with col5:
            capex_cost_eur = st.number_input(
                "Equipment / capex (€)",
                min_value=0.0,
                step=10_000.0,
                value=0.0,
                help="Eligible only for claim years from 2024 onwards.",
            )

        st.divider()

        # ── Eligibility ──────────────────────────────────────────────────────
        st.subheader("Eligibility")
        germany_status = st.radio(
            "Is the company registered (taxable) in Germany? *",
            options=["Yes", "No", "Not sure"],
            index=0,
            horizontal=True,
            help="FZlG requires a German taxable presence (Betriebsstätte). Answering 'Not sure' flags this for consultant review.",
        )

        st.divider()

        # ── Claim year ───────────────────────────────────────────────────────
        st.subheader("Claim year")
        current_year = date.today().year
        claim_year = st.selectbox(
            "Which year are you claiming for? *",
            options=list(range(current_year, current_year - 5, -1)),
            help="FZlG allows retroactive claims up to 4 years back.",
        )

        st.divider()
        compare_prompts = st.checkbox(
            "🔬 Compare v1 vs v2 technical uncertainty prompts (runs both, ~2× slower)",
            value=False,
            help=(
                "Shows the monolithic (v1) and decomposed (v2) prompt outputs side by side. "
                "v2 chains three sub-prompts for a more concrete failure-mode analysis."
            ),
        )

        submitted = st.form_submit_button(
            "Generate Application Draft",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        germany_map = {"Yes": True, "No": False, "Not sure": None}
        _handle_submission(
            company_name=company_name,
            company_description=company_description,
            project_description=project_description,
            team_size=int(team_size),
            rd_time_pct=float(rd_time_pct),
            annual_revenue_eur=annual_revenue_eur,
            personnel_cost_eur=personnel_cost_eur,
            contractor_cost_eur=contractor_cost_eur,
            capex_cost_eur=capex_cost_eur,
            claim_year=int(claim_year),
            is_germany_registered=germany_map[germany_status],
            compare_prompts=compare_prompts,
        )

    st.divider()
    st.caption(
        "Ignite Grant Application Tool — prototype. "
        "Generated content is a drafting aid for qualified consultants; it is not legal or tax advice."
    )


def _handle_submission(*, compare_prompts: bool = False, **kwargs) -> None:
    try:
        application = GrantApplicationInput(**kwargs)
    except ValidationError as exc:
        for err in exc.errors():
            field = " → ".join(str(loc) for loc in err["loc"])
            st.error(f"**{field}**: {err['msg']}")
        return

    calc = calculate(application)

    # ── Eligibility check ─────────────────────────────────────────────────────
    llm, llm_error = _get_llm()
    if llm is None:
        st.error(f"LLM not initialised — {llm_error}")
        return

    with st.spinner("Checking eligibility…"):
        eligibility = evaluate(application, calc, llm)

    _STATUS_ICON = {"pass": "✓", "warn": "⚠", "fail": "✗"}
    verdict_msg = f"**FZlG Eligibility: {eligibility.verdict.value}**"
    if eligibility.verdict == Verdict.ELIGIBLE:
        st.success(verdict_msg)
    elif eligibility.verdict == Verdict.NEEDS_REVIEW:
        st.warning(verdict_msg)
    else:
        st.error(verdict_msg)

    with st.expander(
        "Eligibility detail",
        expanded=(eligibility.verdict != Verdict.ELIGIBLE),
    ):
        for check in eligibility.checks:
            icon = _STATUS_ICON[check.status]
            st.markdown(f"**{icon} {check.name}**  \n{check.reasoning}")
        st.markdown(
            f"**R&D classifier score:** {eligibility.rd_score}/5  \n{eligibility.rd_reasoning}"
        )

    # ── Warnings ──────────────────────────────────────────────────────────────
    if calc.revenue_unknown:
        st.warning(
            "Annual revenue not provided — defaulting to **non-SME rate (25%)**. "
            "If the company qualifies as an SME (<€35M revenue), the credit rate is 35%. "
            "Please verify before submission."
        )
    if calc.capex_excluded:
        st.warning(
            f"Capital expenditure of €{application.capex_cost_eur:,.0f} was entered "
            f"but claim year {application.claim_year} is before 2024 — capex is excluded from eligible costs."
        )
    if calc.is_capped:
        st.warning(
            f"Total eligible costs (€{calc.total_eligible_before_cap:,.0f}) exceed the annual cap "
            f"of €{3_500_000:,.0f}. Credit calculated on the capped amount."
        )

    # ── Cost breakdown ────────────────────────────────────────────────────────
    st.subheader("Indicative cost calculation")
    sme_label = "SME (35%)" if calc.is_sme else "Non-SME (25%)"
    if calc.revenue_unknown:
        sme_label += " — unconfirmed"

    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("SME status", sme_label)
        st.metric("Credit rate", f"{calc.credit_rate:.0%}")
    with col_b:
        st.metric("Total eligible costs", f"€{calc.total_eligible:,.0f}")
        st.metric("Indicative tax credit", f"€{calc.indicative_credit:,.0f}")

    with st.expander("Cost breakdown", expanded=True):
        st.table(
            {
                "Cost category": [
                    "Personnel (100% eligible)",
                    "Contractors (60% eligible)",
                    f"Capex {'(excluded — pre-2024)' if calc.capex_excluded else '(100% eligible from 2024)'}",
                    "**Total eligible (before cap)**",
                    "**Total eligible (after cap)**",
                ],
                "Amount (€)": [
                    f"{calc.eligible_personnel:,.0f}",
                    f"{calc.eligible_contractor:,.0f}",
                    f"{calc.eligible_capex:,.0f}",
                    f"{calc.total_eligible_before_cap:,.0f}",
                    f"{calc.total_eligible:,.0f}",
                ],
            }
        )

    # ── Generated draft ───────────────────────────────────────────────────────
    spinner_msg = (
        "Generating draft (all sections + v1 & v2 uncertainty comparison, ≈45s)…"
        if compare_prompts
        else "Generating draft (all sections, ≈30s)…"
    )
    with st.spinner(spinner_msg):
        try:
            draft = generate_draft(application, calc, llm)
        except LLMCallError as exc:
            st.error(f"Generation failed — {exc}")
            return

    st.subheader("Project summary")
    st.markdown(draft.project_summary)

    st.subheader("Statement of technical uncertainty")
    if not compare_prompts:
        st.markdown(draft.technical_uncertainty)
    else:
        # Run v1 so we can show side-by-side. v2 is already in draft.technical_uncertainty.
        with st.spinner("Running v1 (monolithic) prompt for comparison…"):
            try:
                v1_text = v1_monolithic.generate(application, llm)
            except LLMCallError as exc:
                v1_text = f"⚠ v1 generation failed — {exc}"

        tab_v2, tab_v1 = st.tabs(["v2 — decomposed (default)", "v1 — monolithic"])
        with tab_v2:
            st.caption(
                "Three chained sub-prompts: failure mode → unknowns at outset → synthesis. "
                "Each stage conditions the next."
            )
            st.markdown(draft.technical_uncertainty)
        with tab_v1:
            st.caption(
                "Single prompt covering all three elements at once. "
                "Compare to v2 for concreteness of failure-mode analysis."
            )
            st.markdown(v1_text)

    st.subheader("Qualifying R&D activities")
    st.markdown(draft.qualifying_activities)

    st.subheader("Notes for the consultant")
    st.caption(
        "Deterministic flags (from cost inputs) appear first, followed by LLM-identified "
        "weaknesses and items to verify. Review all before submission."
    )
    st.markdown(draft.consultant_notes)

    st.divider()
    st.download_button(
        label="Download as .docx",
        data=build_docx(application, calc, draft, eligibility),
        file_name=(
            f"FZlG_application_{application.company_name.replace(' ', '_')}_{application.claim_year}.docx"
        ),
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    with st.expander("Validated input (debug)", expanded=False):
        st.json(application.model_dump())


render_form()
