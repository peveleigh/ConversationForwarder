"""Shared test fixtures for Conversation Forwarder tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from typing import Any
from unittest.mock import MagicMock

import pytest
from custom_components.conversation_forwarder.const import CONF_URL, CONF_VERIFY_SSL
from custom_components.conversation_forwarder.conversation import (
    ForwarderConversationEntity,
)
from homeassistant.core import Context, HomeAssistant


@dataclass
class FakeEntry:
    """Minimal stand-in for a ConfigEntry."""

    entry_id: str = "test-entry"
    data: dict[str, Any] = field(default_factory=dict)
    options: dict[str, Any] = field(default_factory=dict)


@pytest.fixture
async def entity() -> AsyncGenerator[ForwarderConversationEntity]:
    """Provide a ForwarderConversationEntity wired to a fake entry."""
    entry = FakeEntry(
        data={CONF_URL: "https://bot.example/endpoint", CONF_VERIFY_SSL: False},
        options={},
    )
    ent = ForwarderConversationEntity(entry)  # type: ignore[arg-type]
    ent.hass = MagicMock(spec=HomeAssistant)
    try:
        yield ent
    finally:
        if ent._http_session is not None and not ent._http_session.closed:
            await ent._http_session.close()


def make_user_input(text: str = "turn on the lights", conversation_id: str | None = None):
    """Build a ConversationInput for tests."""
    from homeassistant.components.conversation import ConversationInput

    return ConversationInput(
        text=text,
        context=Context(),
        conversation_id=conversation_id,
        device_id=None,
        satellite_id=None,
        language="en",
        agent_id="conversation_forwarder.test-entry",
    )
