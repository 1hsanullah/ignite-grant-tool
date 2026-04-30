from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class GrantApplicationInput(BaseModel):
    company_name: str = Field(..., min_length=1)
    company_description: str = Field(..., min_length=10)
    project_description: str = Field(
        ...,
        min_length=50,
        description="Problem, technical uncertainty, novelty — drives the BSFZ narrative",
    )
    team_size: int = Field(..., ge=1)
    rd_time_pct: float = Field(..., ge=1.0, le=100.0)
    annual_revenue_eur: Optional[float] = Field(
        default=None,
        ge=0,
        description="If None, defaults to non-SME rate (25%). SME threshold: <€35M",
    )
    personnel_cost_eur: float = Field(..., ge=0)
    contractor_cost_eur: float = Field(..., ge=0)
    capex_cost_eur: float = Field(
        ...,
        ge=0,
        description="Eligible only for claim years from 2024 onwards",
    )
    claim_year: int
    is_germany_registered: Optional[bool] = Field(
        default=None,
        description=(
            "Whether the company has a German taxable presence (Betriebsstätte). "
            "None ⇒ unconfirmed → surfaces as Needs Review in eligibility."
        ),
    )

    @field_validator("claim_year")
    @classmethod
    def claim_year_in_range(cls, v: int) -> int:
        current = date.today().year
        if v < current - 4 or v > current:
            raise ValueError(
                f"must be between {current - 4} and {current} "
                f"(FZlG allows up to 4 retroactive years)"
            )
        return v

    @property
    def is_sme(self) -> bool:
        """True if annual revenue < €35M — qualifies for the 35% credit rate."""
        if self.annual_revenue_eur is None:
            return False
        return self.annual_revenue_eur < 35_000_000

    @property
    def total_claimed_cost(self) -> float:
        return self.personnel_cost_eur + self.contractor_cost_eur + self.capex_cost_eur
