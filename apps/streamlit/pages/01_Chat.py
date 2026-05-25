from __future__ import annotations

import streamlit as st

from apps.streamlit.client.api_client import ApiClient
from apps.streamlit.ui_design import (
    badge,
    configure_page,
    render_empty_state,
    render_header,
    render_sidebar,
    render_status_grid,
)

configure_page("Chat")
render_sidebar("Chat")
render_header(
    "Chat",
    "Submit DB analysis requests and review routing results without leaving the FastAPI boundary.",
    [("DRAFT", "warning"), ("MANUAL REVIEW REQUIRED", "warning")],
)

client = ApiClient()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_chat_result" not in st.session_state:
    st.session_state.last_chat_result = None
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = ""

render_status_grid(
    [
        ("API base", client.base_url),
        ("Output state", "Draft-only"),
        ("Boundary", "FastAPI client"),
    ]
)

left, right = st.columns([0.38, 0.62], gap="large")

with left:
    st.markdown("#### Conversation")
    st.session_state.conversation_id = st.text_input(
        "Conversation ID",
        value=st.session_state.conversation_id,
        placeholder="Optional existing conversation ID",
    ).strip()
    if not st.session_state.messages:
        render_empty_state("No messages yet", "Enter a DB analysis request to start a reviewed chat run.")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

with right:
    st.markdown("#### Current review")
    result = st.session_state.last_chat_result
    overview_tab, evidence_tab, preview_tab, validation_tab, logs_tab = st.tabs(
        ["Overview", "Evidence", "Preview", "Validation", "Logs"]
    )
    if result is None:
        with overview_tab:
            render_empty_state("Waiting for request", "Routing and validation details will appear here.")
        with evidence_tab:
            render_empty_state("No evidence", "Metadata evidence appears after a routed request.")
        with preview_tab:
            render_empty_state("No preview", "Generated artifacts will be shown separately from chat messages.")
        with validation_tab:
            render_empty_state("No validation", "Policy blockers and warnings remain visible here.")
        with logs_tab:
            st.code("No run logs.", language="text")
    else:
        status = str(result.get("status") or result.get("policyDecision") or "DRAFT").upper()
        intent = str(result.get("intent") or "UNKNOWN")
        route = str(result.get("route") or "blocked")
        blockers = result.get("blockers") if isinstance(result.get("blockers"), list) else []
        error = result.get("error") if isinstance(result.get("error"), dict) else {}
        with overview_tab:
            tone = "danger" if status in {"BLOCKED", "FAILED", "OFFLINE"} else "warning"
            st.markdown(f"{badge(status, tone)} {badge(intent, 'info')}", unsafe_allow_html=True)
            st.write({"intent": intent, "route": route, "policyDecision": result.get("policyDecision")})
            if error:
                st.error(str(error.get("message", "FastAPI request failed.")))
        with evidence_tab:
            st.info("Evidence is retrieved through platform APIs when the route provides it.")
            st.json({"route": route, "evidenceState": "pending"})
        with preview_tab:
            st.markdown(badge("DRAFT", "warning"), unsafe_allow_html=True)
            st.code("Reviewable artifact previews will appear here after runner-backed workflows.", language="text")
        with validation_tab:
            if blockers:
                st.error("Policy blockers are present.")
                st.json({"blockers": blockers})
            elif status in {"FAILED", "OFFLINE"}:
                st.error("The FastAPI request did not complete.")
            else:
                st.success("No policy blockers returned for this chat run.")
        with logs_tab:
            st.json({"resultKeys": sorted(result.keys())})

prompt = st.chat_input("Enter a DB analysis request")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    result = client.create_chat_run(
        prompt,
        conversation_id=st.session_state.conversation_id or None,
    )
    if result.get("conversationId"):
        st.session_state.conversation_id = str(result["conversationId"])
    st.session_state.last_chat_result = result
    route = result.get("route") or "blocked"
    status = result.get("status") or result.get("policyDecision") or "DRAFT"
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": f"Run received. Status: {status}. Route: {route}. Review the tabs for details.",
        }
    )
    st.rerun()
