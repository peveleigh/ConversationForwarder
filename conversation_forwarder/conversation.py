"""Conversation entity that forwards user input to an HTTP endpoint."""

from __future__ import annotations

import logging
from typing import Literal

import aiohttp
from homeassistant.components.conversation import (
    ChatLog,
    ConversationEntity,
    ConversationInput,
    ConversationResult,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent

from .const import (
    CONF_URL,
    CONF_VERIFY_SSL,
    DEFAULT_TIMEOUT,
    DEFAULT_VERIFY_SSL,
)

_LOGGER = logging.getLogger(__name__)

type ForwarderConfigEntry = ConfigEntry[None]


class ForwarderConversationEntity(ConversationEntity):
    """Conversation Forwarder entity.

    Forwards the transcribed user text to a user-supplied HTTP endpoint and
    returns the endpoint's JSON response as speech.
    """

    _attr_has_entity_name = True

    @staticmethod
    def _settings(entry: ForwarderConfigEntry) -> tuple[str, bool]:
        """Return the effective URL and verify_ssl for an entry."""
        url = entry.options.get(CONF_URL, entry.data.get(CONF_URL, ""))
        verify_ssl = entry.options.get(
            CONF_VERIFY_SSL, entry.data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL)
        )
        return str(url), bool(verify_ssl)

    def __init__(self, entry: ForwarderConfigEntry) -> None:
        """Initialize the agent."""
        self._entry = entry
        self._url, self._verify_ssl = self._settings(entry)
        self._http_session: aiohttp.ClientSession | None = None

    @property
    def name(self) -> str | None:
        """Return the name of the entity."""
        return "Conversation Forwarder"

    @property
    def unique_id(self) -> str | None:
        """Return the unique id of the entity."""
        return self._entry.entry_id

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return a list of supported languages."""
        return MATCH_ALL

    @property
    def url(self) -> str:
        """Return the configured endpoint URL."""
        return self._url

    @property
    def http_session(self) -> aiohttp.ClientSession:
        """Return the aiohttp session, creating it on first use."""
        if self._http_session is None or self._http_session.closed:
            self._http_session = aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=self._verify_ssl),
                timeout=aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT),
            )
        return self._http_session

    async def _async_handle_message(
        self,
        user_input: ConversationInput,
        chat_log: ChatLog,
    ) -> ConversationResult:
        """Process a sentence and forward it to the configured endpoint."""
        payload: dict[str, object] = {"query": user_input.text}
        if user_input.conversation_id is not None:
            payload["cid"] = user_input.conversation_id

        _LOGGER.debug("Forwarding user input to endpoint")

        result = await self._forward(payload)

        message = str(result.get("message", ""))
        is_error = result.get("finish_reason") == "error"
        should_continue = bool(result.get("continue_conversation", False)) and not is_error

        intent_response = intent.IntentResponse(language=user_input.language)
        intent_response.async_set_speech(message)

        return ConversationResult(
            response=intent_response,
            conversation_id=user_input.conversation_id,
            continue_conversation=should_continue,
        )

    async def _forward(self, payload: dict[str, object]) -> dict[str, object]:
        """POST the payload to the endpoint and return the parsed JSON result."""
        try:
            async with self.http_session.post(
                self._url, json=payload, raise_for_status=True
            ) as response:
                return await response.json()
        except TimeoutError:
            _LOGGER.warning("Timed out contacting endpoint")
            return self._error("Sorry, the endpoint did not respond in time.")
        except aiohttp.ContentTypeError as err:
            _LOGGER.warning("Endpoint returned a non-JSON response: %s", err)
            return self._error(
                "Sorry, I didn't get a valid JSON response from the endpoint."
            )
        except aiohttp.ClientError as err:
            _LOGGER.warning("Unable to contact endpoint: %s", err)
            return self._error(
                "Sorry, unable to connect to endpoint. Check settings and try again."
            )
        except ValueError as err:
            _LOGGER.warning("Endpoint returned invalid JSON: %s", err)
            return self._error(
                "Sorry, I didn't get a valid JSON response from the endpoint."
            )

    @staticmethod
    def _error(message: str) -> dict[str, object]:
        """Build a fallback error result."""
        return {
            "finish_reason": "error",
            "message": message,
            "continue_conversation": False,
        }

    async def async_will_remove_from_hass(self) -> None:
        """Clean up the HTTP session when the entity is removed."""
        if self._http_session is not None and not self._http_session.closed:
            await self._http_session.close()
            self._http_session = None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ForwarderConfigEntry,
    async_add_entities,
) -> None:
    """Set up the Conversation Forwarder conversation platform."""
    async_add_entities([ForwarderConversationEntity(entry)])
