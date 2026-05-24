from pathlib import Path

import pytest
import yaml

pytest.importorskip("fastapi")

from apps.api.api_app.main import create_app

ROOT = Path(__file__).resolve().parents[2]


def test_openapi_baseline_covers_current_fastapi_routes():
    baseline = yaml.safe_load((ROOT / "spec/development/contract_schema_eval_baseline.yaml").read_text(encoding="utf-8"))
    openapi = yaml.safe_load((ROOT / baseline["openapi"]["path"]).read_text(encoding="utf-8"))
    app = create_app()

    implemented_paths = {
        route.path
        for route in app.routes
        if route.path == "/health" or route.path.startswith("/api/v1/")
    }

    assert set(baseline["openapi"]["implementedPathSubset"]) == implemented_paths
    assert implemented_paths <= set(openapi["paths"])
