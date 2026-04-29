from datetime import date

import streamlit as st
from pydantic import ValidationError

from src.form_schema import GrantApplicationInput


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

        # ── Claim year ───────────────────────────────────────────────────────
        st.subheader("Claim year")
        current_year = date.today().year
        claim_year = st.selectbox(
            "Which year are you claiming for? *",
            options=list(range(current_year, current_year - 5, -1)),
            help="FZlG allows retroactive claims up to 4 years back.",
        )

        submitted = st.form_submit_button(
            "Generate Application Draft",
            type="primary",
            use_container_width=True,
        )

    if submitted:
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
        )

    st.divider()
    st.caption(
        "Ignite Grant Application Tool — prototype. "
        "Generated content is a drafting aid for qualified consultants; it is not legal or tax advice."
    )


def _handle_submission(**kwargs) -> None:
    try:
        application = GrantApplicationInput(**kwargs)
    except ValidationError as exc:
        for err in exc.errors():
            field = " → ".join(str(loc) for loc in err["loc"])
            st.error(f"**{field}**: {err['msg']}")
        return

    st.success("Input validated. Application generation will appear here from Phase 3 onwards.")

    with st.expander("Validated input (debug)", expanded=False):
        st.json(application.model_dump())


render_form()
