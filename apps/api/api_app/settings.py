from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    environment: str = "dev"
    codex_runner_url: str = "http://localhost:8090"
    metadata_gateway_url: str = "http://localhost:8100"


def get_settings() -> Settings:
    return Settings(
        environment=os.getenv("PLF_ENVIRONMENT", "dev"),
        codex_runner_url=os.getenv("PLF_CODEX_RUNNER_URL", "http://localhost:8090"),
        metadata_gateway_url=os.getenv("PLF_METADATA_GATEWAY_URL", "http://localhost:8100"),
    )
