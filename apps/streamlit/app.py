from __future__ import annotations

import streamlit as st

from apps.streamlit.ui_design import configure_page, render_header, render_sidebar, render_status_grid

configure_page("Console")
render_sidebar("Console")
render_header(
    "PLF DB Agent V2",
    "A restrained internal console for DB analysis requests, artifact review, and validation status.",
    [("DRAFT", "warning"), ("API ONLY", "success")],
)

render_status_grid(
    [
        ("UI contract", "DESIGN.md"),
        ("Runtime boundary", "FastAPI only"),
        ("Review posture", "Manual review required"),
    ]
)

overview_tab, workflow_tab, boundary_tab = st.tabs(["Overview", "Workflow", "Boundary"])

with overview_tab:
    st.markdown(
        """
        Use the sidebar pages for chat, history, artifact inspection, and diagnostics.
        The console keeps generated work visible as review material instead of production-ready output.
        """
    )

with workflow_tab:
    st.markdown("#### Review flow")
    st.write("Submit a DB analysis request, review the route and blockers, inspect preview material, then validate before export.")
    st.info("History, artifact detail, validation records, and approval reviews are loaded through FastAPI.")

with boundary_tab:
    st.markdown("#### Safety boundary")
    st.warning("Streamlit does not call DB, MCP, Metadata Gateway, or Service Codex Runner directly.")
    st.code("Streamlit -> FastAPI -> Orchestration / Gateway / Runner", language="text")
