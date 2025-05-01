"""Config flow for NodeRed Conversation integration."""
from __future__ import annotations

import logging
import types
from types import MappingProxyType
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_URL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_URL): str,
    }
)

DEFAULT_OPTIONS = types.MappingProxyType(
    {
        CONF_URL: "",
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> None:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
        
    # TODO Really should attempt a connection. See https://github.com/home-assistant/example-custom-config/blob/master/custom_components/detailed_hello_world_push/config_flow.py
    
    return data


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Conversation forwarder."""
    # TODO remove config flow and use options

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
    #     """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            await validate_input(self.hass, user_input)
            return self.async_create_entry(title="", data=user_input)
            
    #         # except error.APIConnectionError:
    #         #     errors["base"] = "cannot_connect"
    #         # except error.AuthenticationError:
    #         #     errors["base"] = "invalid_auth"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
    #         #     errors["base"] = "unknown"
        else:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlow(config_entry)


# TODO: options currently not used
class OptionsFlow(config_entries.OptionsFlow):
    """Conversation Forwarder config flow options handler."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        #self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            self.hass.config_entries.async_update_entry(self.config_entry, data={CONF_URL: user_input[CONF_URL]})
            return self.async_create_entry(title="", data=user_input)

        schema = cf_config_option_schema(self.config_entry.options)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema),
        )


def cf_config_option_schema(options: MappingProxyType[str, Any]) -> dict:
    """Return a schema for NodeRed completion options."""
    if not options:
        options = DEFAULT_OPTIONS
    return {
        vol.Required(
            CONF_URL,
            description={"suggested_value": options.get(CONF_URL, "")},
            default="",
        ): str,
    }
