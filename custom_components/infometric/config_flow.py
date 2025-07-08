"""Config flow for Infometric integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.const import CONF_URL, CONF_NAME, CONF_USERNAME, CONF_PASSWORD
from homeassistant.helpers import aiohttp_client

from .const import DOMAIN, DEFAULT_NAME

from .infometric import InfometricClient


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Infometric."""

    VERSION = 1
    _options = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                client = InfometricClient(
                    user_input[CONF_URL],
                    user_input[CONF_USERNAME],
                    user_input[CONF_PASSWORD],
                )
                await client.authenticate(
                    aiohttp_client.async_get_clientsession(self.hass)
                )
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )
            except Exception as e:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_URL, default="https://lgh.infometric.se/"): str,
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
                }
            ),
            errors=errors,
        )
