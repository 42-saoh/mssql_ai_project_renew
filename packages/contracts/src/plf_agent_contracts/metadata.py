from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MetadataSearchResult:
    object_type: str
    schema: str
    name: str
    summary: str
    evidence_ref: str
