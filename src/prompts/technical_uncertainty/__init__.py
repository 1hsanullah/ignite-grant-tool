from __future__ import annotations

from src.form_schema import GrantApplicationInput
from src.llm_client import LLMClient
from src.prompts.technical_uncertainty import v1_monolithic, v2_decomposed

__all__ = ["generate", "v1_monolithic", "v2_decomposed"]


def generate(
    application: GrantApplicationInput,
    llm: LLMClient,
    *,
    version: str = "v2",
) -> str:
    if version == "v1":
        return v1_monolithic.generate(application, llm)
    return v2_decomposed.generate(application, llm).synthesis
