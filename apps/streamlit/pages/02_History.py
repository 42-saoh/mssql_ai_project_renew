from __future__ import annotations

import streamlit as st

from apps.streamlit.ui_design import configure_page, render_empty_state, render_header, render_sidebar, render_status_grid

configure_page("History")
render_sidebar("History")
render_header(
    "History",
    "Browse sanitized conversation and artifact history once the G10 store is connected.",
    [("SCAFFOLD", "info"), ("SANITIZED ONLY", "success")],
)

render_status_grid(
    [
        ("Storage policy", "No raw prompts"),
        ("Artifact state", "Review markers visible"),
        ("Backend wiring", "G10"),
    ]
)

overview_tab, artifacts_tab, validation_tab = st.tabs(["Overview", "Artifacts", "Validation"])

with overview_tab:
    render_empty_state("History store pending", "Conversation and chat run records will appear after G10 backend wiring.")

with artifacts_tab:
    st.dataframe(
        [
            {"artifactType": "SP_ANALYSIS_DOC", "state": "DRAFT", "review": "Manual review required"},
            {"artifactType": "DEPENDENCY_REPORT", "state": "VALIDATED", "review": "Evidence reviewed"},
        ],
        width="stretch",
    )

with validation_tab:
    st.warning("Stored records must remain sanitized before they are displayed in this console.")
