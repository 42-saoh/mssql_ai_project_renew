from __future__ import annotations

from pathlib import Path

import yaml

from apps.api.api_app.services.mssql_mcp_client import ALLOWED_METADATA_TOOL_NAMES

ROOT = Path(__file__).resolve().parents[2]


def _load_yaml(rel: str) -> dict:
    return yaml.safe_load((ROOT / rel).read_text(encoding="utf-8"))


def _spec() -> dict:
    return _load_yaml("spec/development/mssql_mcp_metadata_gateway.yaml")


def test_g06_metadata_gateway_contract_files_exist():
    spec = _spec()

    assert spec["scope"] == "g06-mssql-mcp-metadata-gateway"
    assert spec["externalBoundary"]["packagedInThisRepo"] is False
    assert (ROOT / spec["externalBoundary"]["clientModule"]).exists()
    assert (ROOT / spec["externalBoundary"]["serviceModule"]).exists()
    assert (ROOT / spec["externalBoundary"]["routeModule"]).exists()
    assert (ROOT / spec["externalBoundary"]["toolCatalogContract"]).exists()
    assert (ROOT / spec["externalBoundary"]["openapiContract"]).exists()


def test_g06_allowed_tool_contract_matches_client_and_catalog():
    spec = _spec()
    catalog = _load_yaml(spec["externalBoundary"]["toolCatalogContract"])

    expected = set(spec["allowedMetadataTools"]["names"])
    assert expected == ALLOWED_METADATA_TOOL_NAMES
    assert set(catalog["allowedMetadataToolNames"]) == expected
    assert spec["allowedMetadataTools"]["readOnlyOnly"] is True
    assert spec["allowedMetadataTools"]["unknownToolsBlocked"] is True
    assert catalog["catalogPolicy"]["requireReadOnlyFlag"] is True
    assert catalog["catalogPolicy"]["invokeUnknownToolsAllowed"] is False


def test_g06_contract_preserves_metadata_gateway_policy_boundaries():
    spec = _spec()
    blocked = spec["blockedBeforeProxy"]
    response_policy = spec["responsePolicy"]

    assert blocked["rowData"] is True
    assert blocked["storedProcedureExecution"] is True
    assert blocked["freeSqlExecution"] is True
    assert blocked["ddlDmlApply"] is True
    assert blocked["sourceApply"] is True
    assert blocked["deploy"] is True
    assert blocked["rawPrompt"] is True
    assert blocked["rawProviderResponse"] is True
    assert blocked["rawStoredProcedureDefinition"] is True
    assert blocked["secrets"] is True
    assert response_policy["failClosedOnUnsafeResponse"] is True
    assert response_policy["successEnvelopeRequiresRequestedToolName"] is True
    assert response_policy["safeErrorEnvelopeOnly"] is True


def test_g06_metadata_routes_are_declared_in_openapi():
    spec = _spec()
    openapi = _load_yaml(spec["externalBoundary"]["openapiContract"])

    for path in spec["platformRoutes"].values():
        assert path in openapi["paths"]


def test_g06_eval_cases_are_declared():
    spec = _spec()

    for suite, expected_cases in spec["evalCases"].items():
        suite_spec = _load_yaml(f"spec/eval/{suite}.yaml")
        actual_cases = {case["id"] for case in suite_spec["cases"] if "id" in case}
        assert set(expected_cases) <= actual_cases
