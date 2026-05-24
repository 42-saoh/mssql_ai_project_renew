from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("fastapi.testclient")

from fastapi.testclient import TestClient

from apps.api.api_app.main import create_app
from apps.api.api_app.services import metadata_service


def test_metadata_tools_route_proxies_runtime_catalog(monkeypatch):
    monkeypatch.setattr(
        metadata_service,
        "list_metadata_tools",
        lambda: {"tools": [{"name": "search_metadata_objects", "readOnly": True}]},
    )

    response = TestClient(create_app()).get("/api/v1/metadata/tools")

    assert response.status_code == 200
    assert response.json()["tools"][0]["name"] == "search_metadata_objects"


def test_metadata_tool_invoke_route_uses_external_boundary(monkeypatch):
    captured = {}

    def fake_invoke(tool_name, arguments):
        captured["tool_name"] = tool_name
        captured["arguments"] = arguments
        return {"ok": True, "toolName": tool_name}

    monkeypatch.setattr(metadata_service, "invoke_metadata_tool", fake_invoke)

    response = TestClient(create_app()).post(
        "/api/v1/metadata/tools/get_table_schema/invoke",
        json={"arguments": {"dbProfileId": "master", "schema": "dbo", "tableName": "TB_ORDER"}},
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True, "toolName": "get_table_schema"}
    assert captured == {
        "tool_name": "get_table_schema",
        "arguments": {"dbProfileId": "master", "schema": "dbo", "tableName": "TB_ORDER"},
    }


def test_metadata_search_route_maps_to_search_metadata_objects(monkeypatch):
    captured = {}

    def fake_search(query, *, db_profile_id="master", object_types=None, limit=20):
        captured["query"] = query
        captured["db_profile_id"] = db_profile_id
        captured["object_types"] = object_types
        captured["limit"] = limit
        return {"ok": True, "toolName": "search_metadata_objects", "data": {"items": []}}

    monkeypatch.setattr(metadata_service, "search_metadata", fake_search)

    response = TestClient(create_app()).get("/api/v1/metadata/search?q=order&dbProfileId=ppm&limit=3")

    assert response.status_code == 200
    assert response.json()["toolName"] == "search_metadata_objects"
    assert captured == {
        "query": "order",
        "db_profile_id": "ppm",
        "object_types": None,
        "limit": 3,
    }
