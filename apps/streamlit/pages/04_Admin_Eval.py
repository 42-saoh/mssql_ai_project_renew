from __future__ import annotations

import streamlit as st

from apps.streamlit.client.api_client import ApiClient
from apps.streamlit.ui_design import configure_page, render_empty_state, render_header, render_sidebar, render_status_grid

configure_page("Admin / Eval")
render_sidebar("Admin / Eval")
render_header(
    "Admin / Eval",
    "Review diagnostic and eval readiness without exposing raw provider or database payloads.",
    [("DEV ONLY", "warning"), ("DRAFT", "warning")],
)

client = ApiClient()

render_status_grid(
    [
        ("Eval status", "Focused checks"),
        ("Tracing", "Dev gated"),
        ("Policy", "Blocked paths visible"),
    ]
)

checks_tab, observability_tab, logs_tab = st.tabs(["Checks", "Observability", "Logs"])

with checks_tab:
    refresh_diagnostics = st.button("Refresh diagnostics", type="primary")
    health = client.get_health() if refresh_diagnostics else {}
    metadata_ready = client.metadata_ready() if refresh_diagnostics else {}
    metadata_tools = client.list_metadata_tools() if refresh_diagnostics else {}
    health_state = "VALIDATED" if health.get("status") == "ok" else "BLOCKED" if health else "DRAFT"
    metadata_state = "VALIDATED" if metadata_ready.get("ready") is True else "BLOCKED" if metadata_ready else "DRAFT"
    tool_count = len(metadata_tools.get("tools", [])) if isinstance(metadata_tools.get("tools"), list) else 0
    st.dataframe(
        [
            {"check": "FastAPI health", "state": health_state},
            {"check": "Read-only metadata readiness", "state": metadata_state},
            {"check": "Read-only tool catalog", "state": "VALIDATED" if tool_count else "DRAFT"},
            {"check": "Streamlit API-only boundary", "state": "VALIDATED"},
        ],
        use_container_width=True,
    )
    if refresh_diagnostics:
        st.json(
            {
                "health": health,
                "metadataReady": metadata_ready,
                "metadataToolCount": tool_count,
            }
        )
    else:
        render_empty_state("Diagnostics ready", "Refresh to load development status through FastAPI.")

with observability_tab:
    st.info("LangSmith tracing remains disabled unless all development-only flags are explicitly enabled.")
    st.markdown("Raw prompts, raw provider responses, row data, and secrets must not be displayed or stored.")

with logs_tab:
    render_empty_state("No diagnostics logs", "G11 diagnostics will populate this panel after the MVP stage.")
    st.code("Admin/Eval states: VALIDATED, BLOCKED, FAILED.", language="text")
