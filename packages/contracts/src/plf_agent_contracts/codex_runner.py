from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

from .policy import DEFAULT_RUNTIME_POLICY


@dataclass(frozen=True)
class TargetRef:
    dbProfileId: str
    objectType: str
    schema: str
    name: str
    targetKey: str


@dataclass(frozen=True)
class ServiceCodexRunRequest:
    runType: str
    chatRunId: str
    conversationId: str
    target: TargetRef
    toolMode: str = "EVIDENCE_BUNDLE_ONLY"
    skillAllowlist: list[str] = field(default_factory=list)
    outputSchema: str = "service_codex_run_result.schema.json"
    schemaVersion: str = "ServiceCodexRunRequest.v1"
    policy: dict[str, bool] = field(default_factory=lambda: dict(DEFAULT_RUNTIME_POLICY))
    evidenceBundleRef: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ServiceCodexRunResult:
    runType: str
    targetKey: str
    status: str
    artifactProposals: list[dict[str, Any]]
    schemaVersion: str = "ServiceCodexRunResult.v1"
    productionReady: bool = False
    reviewRequired: bool = True
    blockers: list[str] = field(default_factory=list)
    validation: dict[str, Any] = field(default_factory=lambda: {"schemaValid": False, "policyValid": False, "staticValidationPassed": False})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
