from __future__ import annotations

import streamlit as st

from apps.streamlit.ui_design import configure_page, render_empty_state, render_header, render_sidebar, render_status_grid

configure_page("Admin / Eval")
render_sidebar("Admin / Eval")
render_header(
    "Admin / Eval",
    "Review diagnostic and eval readiness without exposing raw provider or database payloads.",
    [("SCAFFOLD", "info"), ("DEV ONLY", "warning")],
)

render_status_grid(
    [
        ("Eval status", "Scaffold"),
        ("Tracing", "Dev gated"),
        ("Policy", "Blocked paths visible"),
    ]
)

checks_tab, observability_tab, logs_tab = st.tabs(["Checks", "Observability", "Logs"])

with checks_tab:
    st.dataframe(
        [
            {"check": "Streamlit API-only boundary", "state": "VALIDATED"},
            {"check": "Design contract", "state": "DRAFT"},
            {"check": "Unsafe wording", "state": "VALIDATED"},
        ],
        width="stretch",
    )

with observability_tab:
    st.info("LangSmith tracing remains disabled unless all development-only flags are explicitly enabled.")

with logs_tab:
    render_empty_state("No diagnostics logs", "G11 diagnostics will populate this panel.")
