from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

from plf_agent_contracts.enums import Intent
from plf_agent_validation.redaction_validator import find_redaction_violations

PGPT_DEFAULT_BASE_URL = "http://aigpt.posco.net/gspgta01-gpt/v1"
PGPT_DEFAULT_MODEL = "gpt-5.4"
PGPT_DEFAULT_TIMEOUT_SECONDS = 30

PGPT_ALLOWED_RESPONSE_PARAMS = {
    "model",
    "input",
    "instructions",
    "stream",
    "temperature",
    "top_p",
    "max_output_tokens",
    "tools",
    "tool_choice",
    "previous_response_id",
    "truncation",
}

PGPT_UNSUPPORTED_FEATURES = {
    "chat.completions",
    "messages",
    "vision",
    "file_search",
    "code_interpreter",
    "audio",
}

_SUPPORTED_INTENTS = {intent.value for intent in Intent}


@dataclass(frozen=True)
class PgptSettings:
    base_url: str = PGPT_DEFAULT_BASE_URL
    model: str = PGPT_DEFAULT_MODEL
    api_key: str = field(default="", repr=False)
    timeout_seconds: int = PGPT_DEFAULT_TIMEOUT_SECONDS
    enabled: bool = False

    @classmethod
    def from_env(cls) -> "PgptSettings":
        api_key = os.getenv("PGPT_API_KEY", "").strip()
        timeout = os.getenv("PGPT_TIMEOUT_SECONDS", str(PGPT_DEFAULT_TIMEOUT_SECONDS)).strip()
        return cls(
            base_url=os.getenv("PGPT_BASE_URL", PGPT_DEFAULT_BASE_URL).strip() or PGPT_DEFAULT_BASE_URL,
            model=os.getenv("PGPT_MODEL", PGPT_DEFAULT_MODEL).strip() or PGPT_DEFAULT_MODEL,
            api_key=api_key,
            timeout_seconds=int(timeout or PGPT_DEFAULT_TIMEOUT_SECONDS),
            enabled=bool(api_key),
        )


@dataclass(frozen=True)
class PgptClassification:
    intent: Intent | None
    confidence: float | None
    reason_summary: str | None
    fallback_reason: str | None = None


@dataclass(frozen=True)
class PgptClientError(Exception):
    code: str
    message: str


def build_pgpt_responses_payload(
    *,
    settings: PgptSettings,
    input_text: str,
    instructions: str,
    **kwargs: Any,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": settings.model,
        "input": input_text,
        "instructions": instructions,
    }
    payload.update({key: value for key, value in kwargs.items() if value is not None})
    _validate_allowed_pgpt_payload(payload)
    return payload


def _validate_allowed_pgpt_payload(payload: dict[str, Any]) -> None:
    unsupported = sorted(set(payload) - PGPT_ALLOWED_RESPONSE_PARAMS)
    if unsupported:
        raise PgptClientError(
            "PGPT_UNSUPPORTED_PARAMETER",
            f"Unsupported PGPT Responses API parameter(s): {', '.join(unsupported)}",
        )
    tools = payload.get("tools")
    if tools is None:
        return
    if not isinstance(tools, list):
        raise PgptClientError("PGPT_UNSUPPORTED_TOOLS", "PGPT tools must be a list of function tools.")
    for tool in tools:
        if not isinstance(tool, dict) or tool.get("type") != "function":
            raise PgptClientError("PGPT_UNSUPPORTED_TOOLS", "Only PGPT function tools are supported.")


def sanitize_reason_summary(reason_summary: str | None, *, original_message: str) -> str | None:
    if not reason_summary:
        return None
    one_line = " ".join(str(reason_summary).split())
    if not one_line:
        return None
    if original_message and original_message.strip() and original_message.strip() in one_line:
        return "PGPT classified the DB analysis request."
    if find_redaction_violations(one_line):
        return "PGPT reason omitted by redaction policy."
    return one_line[:160]


class PgptResponsesClient:
    def __init__(self, settings: PgptSettings | None = None, sdk_client: Any | None = None):
        self.settings = settings or PgptSettings.from_env()
        self._sdk_client = sdk_client

    @classmethod
    def from_env(cls) -> "PgptResponsesClient":
        return cls(PgptSettings.from_env())

    def classify_message(self, message: str) -> PgptClassification:
        if not self.settings.enabled:
            raise PgptClientError("PGPT_DISABLED", "PGPT_API_KEY is not configured.")

        payload = build_pgpt_responses_payload(
            settings=self.settings,
            input_text=message,
            instructions=_classification_instructions(),
            temperature=0,
            max_output_tokens=300,
        )
        response = self._client().responses.create(**payload)
        return self._parse_classification_response(response, original_message=message)

    def _client(self) -> Any:
        if self._sdk_client is not None:
            return self._sdk_client
        try:
            from openai import OpenAI
        except Exception as exc:  # pragma: no cover - exercised only without dependency at runtime
            raise PgptClientError("PGPT_SDK_UNAVAILABLE", "OpenAI SDK is not installed.") from exc
        self._sdk_client = OpenAI(
            api_key=self.settings.api_key,
            base_url=self.settings.base_url,
            timeout=self.settings.timeout_seconds,
        )
        return self._sdk_client

    def _parse_classification_response(self, response: Any, *, original_message: str) -> PgptClassification:
        text = _response_output_text(response)
        try:
            payload = json.loads(text)
        except Exception as exc:
            raise PgptClientError("PGPT_INVALID_RESPONSE", "PGPT classification response was not valid JSON.") from exc
        intent_value = str(payload.get("intent", "")).strip()
        if intent_value not in _SUPPORTED_INTENTS:
            raise PgptClientError("PGPT_INVALID_INTENT", "PGPT returned an unsupported intent.")
        confidence = payload.get("confidence")
        return PgptClassification(
            intent=Intent(intent_value),
            confidence=float(confidence) if isinstance(confidence, int | float) else None,
            reason_summary=sanitize_reason_summary(
                payload.get("reasonSummary"),
                original_message=original_message,
            ),
        )


def _classification_instructions() -> str:
    return (
        "Classify the user request for PLF DB Agent V2. Return only JSON with keys "
        "intent, confidence, reasonSummary. intent must be one of: "
        f"{', '.join(sorted(_SUPPORTED_INTENTS))}. Do not answer general chat. "
        "Do not include raw prompt text, row data, SQL definitions, secrets, or provider metadata."
    )


def _response_output_text(response: Any) -> str:
    if isinstance(response, dict):
        value = response.get("output_text")
    else:
        value = getattr(response, "output_text", None)
    if isinstance(value, str):
        return value
    raise PgptClientError("PGPT_INVALID_RESPONSE", "PGPT response did not include output_text.")
