from __future__ import annotations

from dataclasses import dataclass, field

from .enums import ArtifactType


@dataclass(frozen=True)
class ArtifactProposal:
    artifact_type: ArtifactType
    title: str
    content_markdown: str
    evidence_refs: list[str] = field(default_factory=list)
    review_markers: list[str] = field(default_factory=lambda: ["REVIEW_REQUIRED"])
    production_ready: bool = False
