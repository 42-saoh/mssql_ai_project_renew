from __future__ import annotations

import streamlit as st

from apps.streamlit.client.api_client import ApiClient
from apps.streamlit.ui_design import configure_page, render_empty_state, render_header, render_sidebar, render_status_grid

configure_page("History")
render_sidebar("History")
render_header(
    "History",
    "Browse sanitized conversation, artifact, validation, and review history through FastAPI.",
    [("SANITIZED ONLY", "success"), ("DRAFT", "warning"), ("PENDING REVIEW", "warning")],
)

client = ApiClient()

render_status_grid(
    [
        ("Storage policy", "No raw prompts"),
        ("Artifact state", "Review markers visible"),
        ("Boundary", "FastAPI client"),
    ]
)

conversations_tab, runs_tab, artifacts_tab, approvals_tab, validation_tab = st.tabs(
    ["Conversations", "Runs", "Artifacts", "Approvals", "Validation"]
)

with conversations_tab:
    refresh_conversations = st.button("Refresh conversations", type="primary")
    if not refresh_conversations:
        render_empty_state("Conversation list ready", "Refresh to load sanitized conversation summaries through FastAPI.")
    else:
        conversations = client.list_conversations()
        items = conversations.get("items") if isinstance(conversations.get("items"), list) else []
        if str(conversations.get("status") or "").upper() in {"OFFLINE", "FAILED", "BLOCKED"}:
            st.error("Conversation list is unavailable.")
            st.json(conversations)
        elif items:
            st.dataframe(items, use_container_width=True)
        else:
            render_empty_state("No conversations", "No sanitized conversations were returned.")

with runs_tab:
    conversation_id = st.text_input(
        "Conversation ID",
        placeholder="conv_...",
        key="history_conversation_id",
    ).strip()
    load_history = st.button("Load history")
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

with approvals_tab:
    approval_id = st.text_input(
        "Approval ID",
        placeholder="approval_...",
        key="history_approval_id",
    ).strip()
    approval_cols = st.columns(3)
    with approval_cols[0]:
        refresh_approvals = st.button("Refresh approvals")
    with approval_cols[1]:
        load_approval = st.button("Load review")
    with approval_cols[2]:
        resume_review = st.button("Resume review")

    if refresh_approvals:
        approvals = client.list_approvals()
        items = approvals.get("items") if isinstance(approvals.get("items"), list) else []
        if str(approvals.get("status") or "").upper() in {"OFFLINE", "FAILED", "BLOCKED"}:
            st.error("Approval list is unavailable.")
            st.json(approvals)
        elif items:
            st.dataframe(items, use_container_width=True)
        else:
            render_empty_state("No approvals", "No policy review requests were returned.")
    elif load_approval and approval_id:
        approval = client.get_approval(approval_id)
        if str(approval.get("status") or "").upper() in {"OFFLINE", "FAILED", "NOT_FOUND"}:
            st.error("Approval detail is unavailable.")
        else:
            st.success("Approval review metadata loaded.")
        st.json(approval)
    elif resume_review and approval_id:
        resumed = client.resume_approval(approval_id)
        st.warning("Review was resumed without execution, deployment, or artifact persistence side effects.")
        st.json(resumed)
    else:
        render_empty_state("Approval review ready", "Load or refresh policy review metadata through FastAPI.")

with validation_tab:
    st.warning("Stored records must remain sanitized before they are displayed in this console.")
    st.markdown("`DRAFT`, `VALIDATED`, `BLOCKED`, `FAILED`, `PENDING`, and `RESUMED` states stay visible in API results.")
