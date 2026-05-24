from __future__ import annotations

import streamlit as st

from apps.streamlit.client.api_client import ApiClient

st.title("Chat")
client = ApiClient()

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

prompt = st.chat_input("DB 분석 요청을 입력하세요")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("assistant"):
        result = client.create_chat_run(prompt)
        st.json(result)
    st.session_state.messages.append({"role": "assistant", "content": str(result)})
