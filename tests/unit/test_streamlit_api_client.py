from __future__ import annotations

from apps.streamlit.client.api_client import ApiClient


def test_api_client_prefers_plf_api_base_url(monkeypatch):
    monkeypatch.setenv("PLF_API_BASE_URL", "http://api:8000")
    monkeypatch.setenv("PLF_API_URL", "http://localhost:8000")

    assert ApiClient().base_url == "http://api:8000"


def test_api_client_falls_back_to_plf_api_url(monkeypatch):
    monkeypatch.delenv("PLF_API_BASE_URL", raising=False)
    monkeypatch.setenv("PLF_API_URL", "http://localhost:9000")

    assert ApiClient().base_url == "http://localhost:9000"
