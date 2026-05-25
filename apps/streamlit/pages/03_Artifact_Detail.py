from __future__ import annotations

import json

import streamlit as st

from apps.streamlit.client.api_client import ApiClient
from apps.streamlit.ui_design import badge, configure_page, render_empty_state, render_header, render_sidebar

configure_page("Artifact detail")
render_sidebar("Artifact detail")
render_header(
    "Artifact detail",
    "Inspect reviewable artifact previews, validation results, and export-ready draft metadata.",
    [("DRAFT", "warning"), ("MANUAL REVIEW REQUIRED", "warning")],
)

client = ApiClient()

artifact_id = st.text_input("Artifact ID", placeholder="artifact_...")
load_artifact = st.button("Load artifact", type="primary")
artifact: dict = {}

if load_artifact and artifact_id.strip():
    artifact = client.get_artifact(artifact_id.strip())
elif load_artifact:
    st.warning("Artifact ID is required.")

overview_tab, preview_tab, validation_tab, logs_tab = st.tabs(["Overview", "Preview", "Validation", "Logs"])

with overview_tab:
    refresh = st.button("Refresh artifact list")
    if refresh:
        artifact_list = client.list_artifacts()
        items = artifact_list.get("items") if isinstance(artifact_list.get("items"), list) else []
        if str(artifact_list.get("status") or "").upper() in {"OFFLINE", "FAILED", "BLOCKED"}:
            st.error("Artifact list is unavailable.")
            st.json(artifact_list)
        elif items:
            st.dataframe(items, use_container_width=True)
        else:
            render_empty_state("No artifacts", "FastAPI returned no persisted artifact metadata.")
    if artifact:
        status = str(artifact.get("status") or "DRAFT").upper()
        tone = "danger" if status in {"BLOCKED", "FAILED", "NOT_FOUND", "OFFLINE"} else "warning"
        st.markdown(
            f"{badge(status, tone)} {badge('MANUAL REVIEW REQUIRED', 'warning')}",
            unsafe_allow_html=True,
        )
        st.write(
            {
                "artifactId": artifact.get("artifactId"),
                "artifactType": artifact.get("artifactType"),
                "title": artifact.get("title"),
                "productionReady": artifact.get("productionReady", False),
                "reviewRequired": artifact.get("reviewRequired", True),
            }
        )
    else:
        st.markdown(badge("DRAFT", "warning"), unsafe_allow_html=True)
        render_empty_state("Select an artifact", "Enter an artifact ID or refresh the list to inspect review metadata.")

with preview_tab:
    st.markdown('<div class="agent-code-label">Preview payload</div>', unsafe_allow_html=True)
    preview_payload = artifact or {"artifactType": "SP_ANALYSIS_DOC", "productionReady": False, "reviewRequired": True}
    st.code(json.dumps(preview_payload, indent=2, sort_keys=True), language="json")
    st.download_button(
        "Download preview",
        data=json.dumps(preview_payload, indent=2, sort_keys=True),
        file_name="artifact-preview.json",
        mime="application/json",
    )

with validation_tab:
    if artifact and str(artifact.get("status") or "").upper() in {"NOT_FOUND", "OFFLINE", "FAILED"}:
        st.error("Artifact detail is unavailable.")
        st.json(artifact)
    elif artifact and artifact.get("artifactId"):
        validations = client.list_artifact_validations(str(artifact["artifactId"]))
        items = validations.get("items") if isinstance(validations.get("items"), list) else []
        validation_state = str(artifact.get("validationStatus") or "PENDING").upper()
        st.warning("Generated artifacts must remain draft-only until manual review is complete.")
        st.json(
            {
                "validationStatus": validation_state,
                "reviewMarkers": artifact.get("reviewMarkers", []),
                "evidenceRefs": artifact.get("evidenceRefs", []),
                "contentHash": artifact.get("contentHash"),
                "states": ["VALIDATED", "BLOCKED", "FAILED"],
            }
        )
        if items:
            st.dataframe(items, use_container_width=True)
        else:
            render_empty_state("No validations", "No validation records were returned for this artifact.")
    else:
        st.warning("Generated artifacts must remain draft-only until manual review is complete.")
        st.json(
            {
                "reviewMarkers": artifact.get("reviewMarkers", []),
                "evidenceRefs": artifact.get("evidenceRefs", []),
                "contentHash": artifact.get("contentHash"),
                "states": ["VALIDATED", "BLOCKED", "FAILED"],
            }
        )

with logs_tab:
    st.code("Artifact diagnostics are limited to sanitized FastAPI metadata.", language="text")
