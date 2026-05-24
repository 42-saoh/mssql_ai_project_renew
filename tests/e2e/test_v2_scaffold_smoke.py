from services.codex_runner.runner_app.fake_runner import run_fake


def test_fake_runner_smoke():
    request = {
        "runType": "SP_ANALYSIS",
        "target": {"targetKey": "ppm.PROCEDURE.dbo.X"},
    }
    result = run_fake(request)
    assert result["productionReady"] is False
    assert result["artifactProposals"][0]["reviewMarkers"]
