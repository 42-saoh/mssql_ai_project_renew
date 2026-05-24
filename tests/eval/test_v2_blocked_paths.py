from plf_agent_orchestration.graph import orchestrate_message


def test_ddl_apply_is_not_allowed():
    result = orchestrate_message("이 DDL 적용해줘")
    assert result["policyDecision"] in {"BLOCKED", "BLOCKED_OR_APPROVAL_REQUIRED"}
    assert result["route"] == "blocked"
