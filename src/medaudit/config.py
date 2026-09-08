"""Environment-backed application configuration."""

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime settings that are safe to log after redaction."""

    environment: str = "development"
    log_level: str = "INFO"
    llm_provider: str = "stub"
    llm_model: str = "local-stub"

    @classmethod
    def from_env(cls) -> "Settings":
        """Load non-secret settings from environment variables."""
        return cls(
            environment=os.getenv("MEDAUDIT_ENV", "development"),
            log_level=os.getenv("MEDAUDIT_LOG_LEVEL", "INFO").upper(),
            llm_provider=os.getenv("MEDAUDIT_LLM_PROVIDER", "stub"),
            llm_model=os.getenv("MEDAUDIT_LLM_MODEL", "local-stub"),
        )
