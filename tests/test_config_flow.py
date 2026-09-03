"""Tests for the Conversation Forwarder config flow."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from custom_components.conversation_forwarder import config_flow
from custom_components.conversation_forwarder.const import CONF_URL, CONF_VERIFY_SSL
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType


@pytest.fixture
def hass():
    """Return a lightweight HomeAssistant mock."""
    h = MagicMock(spec=HomeAssistant)
    h.config_entries = MagicMock(spec=config_entries.ConfigEntries)
    return h


async def test_user_step_creates_entry(hass):
    """A valid http URL creates an entry with the provided data."""
    flow = config_flow.ConfigFlow()
    flow.hass = hass
    flow.context = {}

    result = await flow.async_step_user({CONF_URL: "https://bot.example/ep", CONF_VERIFY_SSL: True})

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Conversation Forwarder"
    assert result["data"][CONF_URL] == "https://bot.example/ep"
    assert result["data"][CONF_VERIFY_SSL] is True


async def test_user_step_invalid_url(hass):
    """A non-http(s) URL shows an invalid_url error."""
    flow = config_flow.ConfigFlow()
    flow.hass = hass
    flow.context = {}

    result = await flow.async_step_user({CONF_URL: "ftp://nope", CONF_VERIFY_SSL: True})

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_url"}


async def test_user_step_empty_url(hass):
    """An empty URL shows an invalid_url error."""
    flow = config_flow.ConfigFlow()
    flow.hass = hass
    flow.context = {}

    result = await flow.async_step_user({CONF_URL: "  ", CONF_VERIFY_SSL: True})

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_url"}


async def test_user_step_show_form(hass):
    """With no input the initial form is shown."""
    flow = config_flow.ConfigFlow()
    flow.hass = hass
    flow.context = {}

    result = await flow.async_step_user(None)

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"


async def test_options_flow_creates_options(hass):
    """The options flow writes validated input into entry options."""
    entry = MagicMock(spec=config_entries.ConfigEntry)
    entry.entry_id = "abc"
    entry.data = {CONF_URL: "https://bot.example/ep", CONF_VERIFY_SSL: True}
    entry.options = {}
    flow = config_flow.OptionsFlow(entry)
    flow.hass = hass

    result = await flow.async_step_init({CONF_URL: "https://new.example/bot", CONF_VERIFY_SSL: False})

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_URL] == "https://new.example/bot"
    assert result["data"][CONF_VERIFY_SSL] is False


async def test_options_flow_invalid_url(hass):
    """The options flow rejects an invalid URL."""
    entry = MagicMock(spec=config_entries.ConfigEntry)
    entry.entry_id = "abc"
    entry.data = {CONF_URL: "https://bot.example/ep", CONF_VERIFY_SSL: True}
    entry.options = {}
    flow = config_flow.OptionsFlow(entry)
    flow.hass = hass

    result = await flow.async_step_init({CONF_URL: "not a url", CONF_VERIFY_SSL: True})

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_url"}


async def test_options_flow_show_form(hass):
    """The options flow shows a form with the current URL as suggestion."""
    entry = MagicMock(spec=config_entries.ConfigEntry)
    entry.entry_id = "abc"
    entry.data = {CONF_URL: "https://bot.example/ep", CONF_VERIFY_SSL: True}
    entry.options = {}
    flow = config_flow.OptionsFlow(entry)
    flow.hass = hass

    result = await flow.async_step_init(None)

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"
