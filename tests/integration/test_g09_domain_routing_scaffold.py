from plf_agent_orchestration.graph import orchestrate_message


def test_sp_analysis_routes_to_runner():
    result = orchestrate_message("PPM.dbo.X SP 분석해줘")
    assert result["intent"] == "SP_ANALYSIS"
    assert result["route"] == "codex_runner"


def test_metadata_search_routes_to_gateway():
    result = orchestrate_message("이 컬럼 찾아줘")
    assert result["intent"] == "METADATA_SEARCH"
    assert result["route"] == "metadata_gateway"


def test_general_chat_is_blocked():
    result = orchestrate_message("시를 써줘")
    assert result["intent"] == "BLOCKED"
    assert result["route"] == "blocked"
