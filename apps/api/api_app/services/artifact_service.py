from __future__ import annotations


def persist_artifact_after_validation(proposal: dict) -> dict:
    if proposal.get("productionReady") is True:
        raise ValueError("productionReady=true artifacts are blocked")
    return {"status": "persisted", "artifact": proposal}
