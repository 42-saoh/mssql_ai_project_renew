import pytest

from plf_agent_contracts.enums import Intent
from plf_agent_orchestration.intents import classify_intent


@pytest.mark.parametrize(
    "message",
    [
        "run stored procedure dbo.ProcessOrder",
        "call procedure dbo.ProcessOrder",
        "exec dbo.ProcessOrder",
        "exec dbo.ProcessOrder;",
        "exec dbo.*",
        "call [dbo].[ProcessOrder]",
        "execute proc dbo.ProcessOrder",
        "execute procedure dbo.ProcessOrder",
        "SP execution for dbo.ProcessOrder",
        "\uc800\uc7a5 \ud504\ub85c\uc2dc\uc800 \uc2e4\ud589\ud574\uc918",
        "\uc800\uc7a5 \ud504\ub85c\uc2dc\uc800\ub97c \ud638\ucd9c\ud574\uc918",
        "\ud504\ub85c\uc2dc\uc800 \ud638\ucd9c\ud574\uc918",
        "\ud504\ub85c\uc2dc\uc800\ub97c \uc2e4\ud589\ud574\uc918",
        "SP \uc2e4\ud589\ud574\uc918",
        "SP\ub97c \uc2e4\ud589\ud574\uc918",
    ],
)
def test_stored_procedure_execution_phrases_are_blocked(message):
    assert classify_intent(message) == Intent.BLOCKED_OR_APPROVAL_REQUIRED
