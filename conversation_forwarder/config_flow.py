"""Config flow for the Conversation Forwarder integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_URL, CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class InvalidUrlError(Exception):
    """Raised when the provided endpoint URL is invalid."""


def _url_schema(default: str | None = None) -> vol.Schema:
    """Schema for the URL + verify_ssl step."""
    schema: dict[vol.Required | vol.Optional, Any] = {
        vol.Required(CONF_URL, description={"suggested_value": default}): str,
        vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): bool,
    }
    return vol.Schema(schema)


async def _validate_input(hass: HomeAssistant, data: dict[str, Any]) -> None:
    """Validate the user input.

    Raises InvalidUrlError if the URL is malformed or not an http(s) URL.
    """
    url = str(data[CONF_URL]).strip()
    if not url:
        raise InvalidUrlError
    from urllib.parse import urlparse

    result = urlparse(url)
    if result.scheme not in ("http", "https") or not result.netloc:
        raise InvalidUrlError


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Conversation Forwarder."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=_url_schema())

        errors: dict[str, str] = {}
        try:
            await _validate_input(self.hass, user_input)
        except InvalidUrlError:
            errors["base"] = "invalid_url"
        else:
            return self.async_create_entry(title="Conversation Forwarder", data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=_url_schema(user_input.get(CONF_URL)), errors=errors
        )

    async def async_get_options_flow(
        self, config_entry: ConfigEntry
    ) -> OptionsFlow:
        """Create the options flow."""
        return OptionsFlow(config_entry)


class OptionsFlow(config_entries.OptionsFlow):
    """Conversation Forwarder options handler."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        current_url = self._config_entry.options.get(
            CONF_URL, self._config_entry.data.get(CONF_URL, "")
        )

        if user_input is not None:
            errors: dict[str, str] = {}
            try:
                await _validate_input(self.hass, user_input)
            except InvalidUrlError:
                errors["base"] = "invalid_url"
            else:
                return self.async_create_entry(title="", data=user_input)

            return self.async_show_form(
                step_id="init",
                data_schema=_url_schema(user_input.get(CONF_URL)),
                errors=errors,
            )

        return self.async_show_form(
            step_id="init",
            data_schema=_url_schema(str(current_url)),
        )
