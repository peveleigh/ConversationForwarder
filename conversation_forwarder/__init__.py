"""The Forwarder Conversation integration."""

# This code is from nodered_conversation and then modified for my needs
# https://github.com/roblandry/nodered_conversation
from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Literal

import aiohttp
from homeassistant.components import conversation
from homeassistant.const import MATCH_ALL
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import intent

from .const import (
    CONF_URL,
    DOMAIN,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import (
        HomeAssistant,
    )

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Conversation Forwarderfrom a config entry."""
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = entry.data[CONF_URL]

    _LOGGER.info("entry.data: %s", entry.data)

    conversation.async_set_agent(hass, entry, CFAgent(hass, entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload entry."""
    hass.data[DOMAIN].pop(entry.entry_id)

    conversation.async_unset_agent(hass, entry)
    return True


class CFAgent(conversation.AbstractConversationAgent):
    """Conversation Forwarder agent."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the agent."""
        self.hass = hass
        self.entry = entry
        self.url=entry.data[CONF_URL]
        _LOGGER.debug("configUrl %s", entry.data[CONF_URL])

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return a list of supported languages."""
        return MATCH_ALL

    async def call_get_request(self, url: str, params: dict) -> str:
        """Connect to agent server."""
        async with(
             aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) \
                as session,
            session.get(url, params=params) as response,
        ):
            text = await response.text()
            _LOGGER.info("Post Result text: %s", text)
            return text

    async def async_process(
        self, user_input: conversation.ConversationInput,
    ) -> conversation.ConversationResult:
        """Process a sentence."""
        content = {"query": user_input.text}

        _LOGGER.debug("Content sent to endpoint %s", content)

        try:
            _LOGGER.info("url: %s", self.url)
            result_req = await self.call_get_request(self.url, content)
            result = json.loads(result_req)
        except aiohttp.ClientError:
            _LOGGER.warning("Unable to connect to endpoint %s", self.url)
            result = {
                "finish_reason": "error",
                "message": "Sorry, unable to connect to endpoint. Check settings and\
                     try again.",
            }
        except json.decoder.JSONDecodeError as e:
            _LOGGER.warning("Something happened: %s", e)
            _LOGGER.warning("Result: %s", result_req)
            result = {
                "finish_reason": "error",
                "message": "Sorry, I didn't get a response from endpoint. \
                    Check your logs for possible issues.",
            }

        _LOGGER.debug("Result %s", result)

        # https://github.com/home-assistant/core/blob/220aaf93c6b0d201bb4baa59d96ff9d9c8a66279/homeassistant/helpers/intent.py#L1380
        intent_response = intent.IntentResponse(language=user_input.language)

        should_continue = False
        intent_response.async_set_speech(result)

        _LOGGER.debug("should_continue %s", should_continue)
        # https://github.com/home-assistant/core/blob/eb3cb0e0c7835ca10cdbb225d85f5e22d512e290/homeassistant/components/conversation/models.py#L60
        return conversation.ConversationResult(
            response=intent_response,
            conversation_id=user_input.conversation_id,
            continue_conversation=should_continue,
        )

