from __future__ import annotations

import streamlit as st

from apps.streamlit.ui_design import badge, configure_page, render_empty_state, render_header, render_sidebar

configure_page("Artifact detail")
render_sidebar("Artifact detail")
render_header(
    "Artifact detail",
    "Inspect reviewable artifact previews, validation results, and export-ready draft files.",
    [("DRAFT", "warning"), ("MANUAL REVIEW REQUIRED", "warning")],
)

overview_tab, preview_tab, validation_tab, logs_tab = st.tabs(["Overview", "Preview", "Validation", "Logs"])

with overview_tab:
    st.markdown(badge("DRAFT", "warning"), unsafe_allow_html=True)
    render_empty_state("Select an artifact", "Artifact content will appear after history and artifact APIs are wired.")

with preview_tab:
    st.markdown('<div class="agent-code-label">Preview payload</div>', unsafe_allow_html=True)
    st.code('{"artifactType": "SP_ANALYSIS_DOC", "productionReady": false}', language="json")
    st.download_button(
        "Download preview",
        data='{"artifactType": "SP_ANALYSIS_DOC", "productionReady": false}',
        file_name="artifact-preview.json",
        mime="application/json",
    )

with validation_tab:
    st.warning("Generated artifacts must remain draft-only until manual review is complete.")

with logs_tab:
    st.code("No artifact logs.", language="text")
