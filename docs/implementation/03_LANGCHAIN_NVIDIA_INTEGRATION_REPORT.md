# Prompt 3 Implementation Report: LangChain + NVIDIA Provider Integration

Date: 2026-07-31

## Summary

Prompt 3 is implemented on top of the Prompt 1 deterministic backend and Prompt 2 persistence/API contract. The old generic direct-HTTP narrative provider was removed from the app path and replaced with a bounded LangChain provider that uses `langchain_nvidia_ai_endpoints.ChatNVIDIA`.

The deterministic report remains the only source of financial truth. The model receives a safe, precomputed report context plus approved trace placeholders; it can only return structured narrative sections and unavailable metrics. Every provider result is validated and rendered through the existing trace validator before persistence or response. Invalid, missing, timed out, or unavailable provider output falls back to deterministic text.

## Files Changed

- `backend/app/agent/`: new provider boundary, strict schemas, prompt template, safe context builder, and NVIDIA implementation.
- `backend/app/services/narrative_service.py`: narrative generation is now async and consumes `generate_draft(...)` provider results.
- `backend/app/api/routes_narratives.py`: `POST /narrative` is async.
- `backend/app/main.py`: app wiring builds `ChatNVIDIANarrativeProvider` when enabled, without creating a network client at startup.
- `backend/app/integrations/llm_provider.py`: compatibility export only; no direct LLM HTTP implementation remains.
- `backend/app/core/config.py` and `backend/.env.example`: NVIDIA configuration, safe missing-key behavior, and bounded settings.
- `backend/tests/`: non-live fake-provider coverage and optional gated live NVIDIA smoke test.
- `backend/pyproject.toml` and `backend/requirements.txt`: LangChain/NVIDIA dependencies and `live_nvidia` pytest marker.

## Verified API Usage

Official/current usage was checked before implementation using Context7 documentation for `langchain-nvidia-ai-endpoints` and `langchain-core`, then verified locally by introspection after installing the packages.

Installed versions:

- `langchain-core==1.5.3`
- `langchain-nvidia-ai-endpoints==1.4.3`
- `pytest-asyncio==1.3.0`

Relevant local signatures confirmed:

- `ChatNVIDIA(..., model=None, nvidia_api_key=None, api_key=None, base_url=None, temperature=None, max_completion_tokens=None, ...)`
- `ChatNVIDIA.with_structured_output(schema, include_raw=False, **kwargs)`

Implementation usage:

- `ChatPromptTemplate.from_messages([...])`
- `prompt | ChatNVIDIA(...).with_structured_output(NarrativeDraft)`
- async `ainvoke(...)` inside `asyncio.timeout(...)`
- `max_completion_tokens` for bounded output size
- `nvidia_api_key` from `SecretStr`

## Safety Controls

- No OpenAI, Anthropic, Google, LangGraph, CrewAI, AutoGen, ReAct agent, vector database, frontend, auth, or unrelated framework was added.
- `ChatNVIDIA` is imported lazily only when generation is attempted.
- App startup succeeds without `NVIDIA_API_KEY`.
- Missing key returns deterministic fallback with `PROVIDER_NOT_CONFIGURED`.
- Provider errors are categorized as disabled, not configured, timeout, rate-limited, unavailable, invalid response, or authentication.
- Provider output uses strict Pydantic models with `extra="forbid"`, bounded section counts, bounded text length, bounded trace keys, and bounded unavailable metrics.
- Raw visits, rejected raw rows, and API keys are not placed in the model input.
- Repositories and deterministic report services do not import LangChain/provider code.
- Cached current narratives skip provider calls.
- Force regeneration calls the provider.
- If the report hash changes while generation is in progress, the outdated result is rejected with `NARRATIVE_REPORT_CHANGED` and is not saved.
- Prompt 4 repair/grounding expansion was intentionally deferred; Prompt 3 preserves existing validation and fallback behavior.

## Configuration

Configured logical defaults:

```env
LLM_ENABLED=true
LLM_PROVIDER=nvidia
NVIDIA_API_KEY=
NVIDIA_MODEL=nvidia/nemotron-3-nano-30b-a3b
NVIDIA_BASE_URL=
LLM_TIMEOUT_SECONDS=25
LLM_MAX_TOKENS=700
LLM_TEMPERATURE=0
LLM_TRANSPORT_RETRIES=1
```

`NVIDIA_API_KEY` is modeled as `SecretStr`; representations do not expose the secret.

## Tests Added

- Settings bounds and secret masking.
- Startup/provider construction without network initialization.
- Lazy `ChatNVIDIA` construction.
- `ChatNVIDIA` constructor parameters.
- Async-only provider invocation.
- Timeout handling.
- Authentication, rate-limit, and unavailable classification.
- Invalid structured output rejection.
- Strict output schema rejection of extra/unstructured output.
- Safe model input exclusion of raw visit IDs and raw rejected rows.
- Missing-key deterministic fallback.
- Valid fake provider generation, caching, and force regeneration.
- Invalid provider grounding fallback without persisting raw output.
- Stale report-hash generation rejection.
- Optional `live_nvidia` smoke test gated by `NVIDIA_API_KEY` and `RUN_LIVE_NVIDIA_TESTS=1`.

## Verification Status

Final verification performed on 2026-07-31:

```bash
python -m pip check
```

Result: failed because `python` is not on PATH on this machine (`zsh:1: command not found: python`). The same is true for the exact `python -c ...ChatNVIDIA...` command. `python3` is the available interpreter.

```bash
python3 -m pip check
```

Result: failed due to pre-existing global environment conflicts outside this project, including incompatible `websockets` requirements between `alpaca-trade-api` (`<11`) and `google-adk` (`>=15,<16`). The project test/import checks below pass despite those machine-wide package conflicts.

```bash
python3 -c "from langchain_nvidia_ai_endpoints import ChatNVIDIA; print('ChatNVIDIA import successful')"
```

Result: passed.

```bash
python3 -m pytest -m "not live_nvidia" -q
```

Result: `66 passed, 1 deselected`.

```bash
python3 -m pytest -m "not live_nvidia" --cov=app --cov-branch --cov-report=term-missing --cov-fail-under=90
```

Result: `66 passed, 1 deselected`, total branch coverage `93.56%`.

```bash
python3 -c "from app.main import create_app; create_app(); print('app import successful')"
```

Result: passed.

```bash
DATABASE_URL=sqlite:////tmp/swasthiq_prompt3_migration_gate.db python3 -m alembic upgrade head
```

Result: passed. No Prompt 3 schema migration was required.

```bash
python3 -c "import json; from pathlib import Path; from app.main import create_app; app = create_app(); path = Path('../docs/contracts/openapi.json'); path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(app.openapi(), indent=2, sort_keys=True), encoding='utf-8'); print('generated', path)"
```

Result: passed.

```bash
python3 -m pytest -m live_nvidia -q
```

Result: `1 skipped`; live NVIDIA execution is gated by `NVIDIA_API_KEY` and `RUN_LIVE_NVIDIA_TESTS=1`.

```bash
git diff --check
```

Result: passed.

No formatter/linter config exists beyond the pytest/coverage checks above.
