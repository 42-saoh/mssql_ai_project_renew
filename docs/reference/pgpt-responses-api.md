# PGPT Responses API Contract

PLF DB Agent V2 uses PGPT only in the user-chat orchestration boundary. PGPT is an OpenAI-compatible Responses API proxy, but it must not be treated as the full OpenAI public API.

## Configuration

Use environment variables only:

- `PGPT_BASE_URL`, default `http://aigpt.posco.net/gspgta01-gpt/v1`
- `PGPT_MODEL`, default `gpt-5.4`
- `PGPT_API_KEY`, required to enable PGPT calls
- `PGPT_TIMEOUT_SECONDS`, default `30`

## Allowed Responses API Parameters

Only these request parameters may be used:

- `model`
- `input`
- `instructions`
- `stream`
- `temperature`
- `top_p`
- `max_output_tokens`
- `tools`
- `tool_choice`
- `previous_response_id`
- `truncation`

`tools` may contain only function tools with `type: "function"`.

## Unsupported Or Unverified Features

Do not use Chat Completions, `messages`, vision, files, code interpreter, audio, or arbitrary OpenAI Responses API extensions unless PGPT support is explicitly verified and the allowlist is updated with tests.

## Safety Rules

- PGPT is optional; if it is unavailable or unconfigured, orchestration must fall back to deterministic intent classification.
- Policy gates run before PGPT calls. Blocked or out-of-domain requests must not be sent to PGPT.
- Do not persist raw prompts, raw provider responses, row data, SQL definitions, secrets, or API keys.
- Orchestration responses may include safe PGPT metadata such as `pgptUsed`, `pgptModel`, `pgptFallbackReason`, and a sanitized `pgptReasonSummary`.
