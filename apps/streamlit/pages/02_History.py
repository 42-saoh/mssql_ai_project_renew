from __future__ import annotations

import streamlit as st

from apps.streamlit.client.api_client import ApiClient
from apps.streamlit.ui_design import configure_page, render_empty_state, render_header, render_sidebar, render_status_grid

configure_page("History")
render_sidebar("History")
render_header(
    "History",
    "Browse sanitized conversation and artifact history through FastAPI.",
    [("SANITIZED ONLY", "success"), ("DRAFT", "warning")],
)

client = ApiClient()

render_status_grid(
    [
        ("Storage policy", "No raw prompts"),
        ("Artifact state", "Review markers visible"),
        ("Boundary", "FastAPI client"),
    ]
)

overview_tab, artifacts_tab, validation_tab = st.tabs(["Overview", "Artifacts", "Validation"])

with overview_tab:
    conversation_id = st.text_input(
        "Conversation ID",
        placeholder="conv_...",
        key="history_conversation_id",
    ).strip()
    load_history = st.button("Load history", type="primary")
    if not load_history:
        render_empty_state("History lookup ready", "Enter a conversation ID to load sanitized run history through FastAPI.")
    elif not conversation_id:
        st.warning("Conversation ID is required.")
    else:
        conversation = client.get_conversation(conversation_id)
        status = str(conversation.get("status") or "VALIDATED").upper()
        if status in {"OFFLINE", "FAILED", "NOT_FOUND"}:
            st.error(f"History lookup status: {status}")
            st.json(conversation)
        else:
            st.success("Sanitized conversation history loaded.")
            st.write(
                {
                    "conversationId": conversation.get("conversationId"),
                    "title": conversation.get("title"),
                }
            )
            items = conversation.get("items") if isinstance(conversation.get("items"), list) else []
            if items:
                st.dataframe(items, use_container_width=True)
            else:
                render_empty_state("No chat runs", "No sanitized chat runs were returned for this conversation.")

with artifacts_tab:
    refresh_artifacts = st.button("Refresh artifacts")
    if not refresh_artifacts:
        render_empty_state("Artifact list ready", "Refresh to load sanitized artifact metadata through FastAPI.")
    else:
        artifact_list = client.list_artifacts()
        items = artifact_list.get("items") if isinstance(artifact_list.get("items"), list) else []
        if str(artifact_list.get("status") or "").upper() in {"OFFLINE", "FAILED", "BLOCKED"}:
            st.error("Artifact list is unavailable.")
            st.json(artifact_list)
        elif items:
            st.dataframe(items, use_container_width=True)
        else:
            render_empty_state("No artifacts", "No persisted artifact metadata was returned.")

with validation_tab:
    st.warning("Stored records must remain sanitized before they are displayed in this console.")
    st.markdown("`DRAFT`, `VALIDATED`, `BLOCKED`, and `FAILED` states stay visible in API results.")
