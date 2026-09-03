# AGENTS.md

## Project overview
ConversationForwarder is a Home Assistant custom component (`custom_components/conversation_forwarder`) that routes voice-assistant conversations to a user-supplied HTTP endpoint. It is a thin integration: the agent POSTs the transcribed user text as JSON and returns the endpoint's JSON response as speech.

Forked from [jimrush's ConversationForwarder](https://github.com/jimrushPersonal/ConversationForwarder) and [roblandry's nodered_conversation](https://github.com/roblandry/nodered_conversation).

## Layout
All integration code lives under `conversation_forwarder/` (this is what gets copied into HA's `custom_components/`):

- `__init__.py` — `async_setup_entry` / `async_unload_entry`; forwards setup to the `conversation` platform and registers an options-update listener that reloads the entry.
- `conversation.py` — `ForwarderConversationEntity` (a `ConversationEntity` subclass) implementing `_async_handle_message`. Request forwarding (POST) and response mapping happen here. Manages a per-entity `aiohttp.ClientSession` (lazily created, closed in `async_will_remove_from_hass`).
- `config_flow.py` — `ConfigFlow` writes URL + `verify_ssl` to entry `data`; `OptionsFlow` writes to entry `options`. Reads use options-first-then-data via `_settings`.
- `const.py` — `DOMAIN` (`"conversation_forwarder"`), `CONF_URL` (`"server_url"`), `CONF_VERIFY_SSL` (`"verify_ssl"`), `DEFAULT_VERIFY_SSL` (True), `DEFAULT_TIMEOUT` (30).
- `manifest.json` — `integration_type: service`, `iot_class: local_push`, depends on `conversation`. `version` starts at `0.1.0`; bump it when releasing.
- `strings.json` / `translations/en.json` — UI strings for the config/options flows. `services.yaml` is empty.

## Development commands
Setup and verification (CI runs the same in `.github/workflows/ci.yml`):
```
uv sync --dev
uv run ruff check .
uv run pytest -q
```
Run a single test file: `uv run pytest tests/test_conversation_entity.py -q`.

- **Python 3.13.2+ required** (`requires-python = ">=3.13.2,<3.14"` in `pyproject.toml`; ruff `target-version = "py313"`). Note: the CI workflow currently runs `uv python install 3.12`, which is stale — local dev should use 3.13.
- **pytest `asyncio_mode = "auto"`** (`pyproject.toml`): async tests/fixtures need no `@pytest.mark.asyncio` decorator.
- **Root `conftest.py`** registers a synthetic `custom_components` package pointing at the repo root, so `conversation_forwarder/` is importable as `custom_components.conversation_forwarder` in tests. Do not delete it.
- **`tests/conftest.py`** provides an async `entity` fixture (a `ForwarderConversationEntity` wired to a `FakeEntry`) and a `make_user_input()` helper. HTTP is mocked with **`aioresponses`** — do not make real network calls in tests.

## Runtime contract
- HA minimum: 2025.4+ (uses `ConversationEntity` / `_async_handle_message` and the `continue_conversation` flag on `ConversationResult`). Tests pin `homeassistant==2025.12.5` plus matching `hassil` / `home-assistant-intents`.
- Request: `POST <configured URL>` with JSON body `{"query": <user text>, "cid": <conversation_id>?}` (cid only when a conversation_id exists). `raise_for_status=True`, so non-2xx raises. SSL verification configurable via `verify_ssl` (default True). `ClientTimeout(total=DEFAULT_TIMEOUT=30s)`.
- Response: JSON with `finish_reason` (string), `message` (string, spoken to user), `continue_conversation` (bool). Extra fields ignored.
- `continue_conversation` is honored from the endpoint unless `finish_reason == "error"`, in which case it is forced `False`.
- On `TimeoutError`, `aiohttp.ClientError` (incl. `ContentTypeError`), or `ValueError` (invalid JSON), a fallback error message is returned with `finish_reason: "error"`. Short reasons logged at `warning`; URLs and response bodies at `debug` only.

## Conventions
- Python, async throughout (`async def` entry points, `aiohttp` for HTTP).
- `from __future__ import annotations` at the top of modules; type-only HA imports guarded under `if TYPE_CHECKING:`.
- Module-level `_LOGGER = logging.getLogger(__name__)`; log via `_LOGGER.info/debug/warning`.
- Constants live in `const.py`; import them rather than hardcoding `DOMAIN`/`CONF_URL`.
- Ruff line-length is 100 but `E501` is ignored, so line length is not enforced; the other selected rules (`E,F,W,I,UP,B,SIM,RUF`) are.
- Keep docstrings (triple-quoted) when editing.
