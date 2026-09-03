"""Tests for the Conversation Forwarder conversation entity."""

from __future__ import annotations

import aiohttp
from aioresponses import aioresponses
from custom_components.conversation_forwarder.const import CONF_URL, CONF_VERIFY_SSL
from custom_components.conversation_forwarder.conversation import (
    ForwarderConversationEntity,
)

from conftest import make_user_input

ENDPOINT = "https://bot.example/endpoint"


async def _run(entity: ForwarderConversationEntity, text: str = "hi", cid: str | None = None):
    """Invoke the handler and return (speech, continue_conversation)."""
    result = await entity._async_handle_message(make_user_input(text, cid), chat_log=None)
    speech = result.response.speech.get("plain", {}).get("speech", "")
    return speech, result.continue_conversation


async def test_success_message_and_continue(entity):
    """A valid JSON response sets speech to message and honors continue_conversation."""
    with aioresponses() as m:
        m.post(
            ENDPOINT,
            payload={
                "finish_reason": "stop",
                "message": "The lights are on",
                "continue_conversation": True,
            },
        )
        speech, cont = await _run(entity)

    assert speech == "The lights are on"
    assert cont is True


async def test_success_no_continue_flag_defaults_false(entity):
    """Missing continue_conversation defaults to False."""
    with aioresponses() as m:
        m.post(ENDPOINT, payload={"finish_reason": "stop", "message": "done"})
        speech, cont = await _run(entity)

    assert speech == "done"
    assert cont is False


async def test_error_finish_reason_forces_no_continue(entity):
    """finish_reason == error overrides continue_conversation."""
    with aioresponses() as m:
        m.post(
            ENDPOINT,
            payload={
                "finish_reason": "error",
                "message": "boom",
                "continue_conversation": True,
            },
        )
        speech, cont = await _run(entity)

    assert speech == "boom"
    assert cont is False


async def test_http_error_returns_fallback(entity):
    """A 5xx response yields an error result and does not raise."""
    with aioresponses() as m:
        m.post(ENDPOINT, status=500, body="server down")
        speech, cont = await _run(entity)

    assert "unable to connect" in speech.lower()
    assert cont is False


async def test_non_json_content_type(entity):
    """A non-JSON body produces a JSON-parse error result."""
    with aioresponses() as m:
        m.post(
            ENDPOINT,
            status=200,
            body="not json at all",
            headers={"Content-Type": "text/plain"},
        )
        speech, cont = await _run(entity)

    assert "valid json" in speech.lower()
    assert cont is False


async def test_invalid_json_body(entity):
    """A 200 response with invalid JSON produces a JSON error result."""
    with aioresponses() as m:
        m.post(
            ENDPOINT,
            status=200,
            body="{not valid json",
            headers={"Content-Type": "application/json"},
        )
        speech, cont = await _run(entity)

    assert "valid json" in speech.lower()
    assert cont is False


async def test_timeout(entity):
    """A request timeout yields a timeout error result."""
    with aioresponses() as m:
        m.post(ENDPOINT, exception=TimeoutError())
        speech, cont = await _run(entity)

    assert "did not respond" in speech.lower()
    assert cont is False


async def test_connection_error(entity):
    """A connection error yields a connect error result."""
    with aioresponses() as m:
        m.post(ENDPOINT, exception=aiohttp.ClientConnectionError("no route"))
        speech, cont = await _run(entity)

    assert "unable to connect" in speech.lower()
    assert cont is False


async def test_conversation_id_sent_in_payload(entity):
    """When a conversation_id is present it is forwarded as cid."""
    seen: dict[str, object] = {}

    async def handler(url, **kwargs):
        seen.update(kwargs.get("json", {}))
        from aioresponses.core import CallbackResult

        return CallbackResult(payload={"finish_reason": "stop", "message": "ok"})

    with aioresponses() as m:
        m.post(ENDPOINT, callback=handler)
        await _run(entity, text="hello", cid="conv-123")

    assert seen.get("query") == "hello"
    assert seen.get("cid") == "conv-123"


async def test_no_cid_without_conversation_id(entity):
    """Without a conversation_id the payload omits cid."""
    seen: dict[str, object] = {}

    async def handler(url, **kwargs):
        seen.update(kwargs.get("json", {}))
        from aioresponses.core import CallbackResult

        return CallbackResult(payload={"finish_reason": "stop", "message": "ok"})

    with aioresponses() as m:
        m.post(ENDPOINT, callback=handler)
        await _run(entity)

    assert "cid" not in seen
    assert seen.get("query") == "hi"


async def test_options_override_data_url(entity):
    """Entry options take precedence over data for the effective URL."""
    entity._entry.options = {CONF_URL: "https://other.example/bot", CONF_VERIFY_SSL: False}
    entity._url, entity._verify_ssl = ForwarderConversationEntity._settings(
        entity._entry
    )
    with aioresponses() as m:
        m.post("https://other.example/bot", payload={"message": "switched", "finish_reason": "stop"})
        speech, cont = await _run(entity)

    assert speech == "switched"
    assert cont is False
