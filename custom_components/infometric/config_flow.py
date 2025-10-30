"""Config flow for Infometric integration."""
from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.const import CONF_URL, CONF_NAME, CONF_USERNAME, CONF_PASSWORD
from homeassistant.helpers import aiohttp_client

from .const import DOMAIN, DEFAULT_NAME, DEFAULT_URL

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
            # Validate and normalize URL using urlparse
            try:
                parsed_url = urlparse(user_input[CONF_URL])
                if not parsed_url.scheme or not parsed_url.netloc:
                    errors["base"] = "invalid_url"
                else:
                    normalized_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path.rstrip('/')}"
                    
                    # Uniqueness check: same URL + username
                    for entry in self._async_current_entries():
                        entry_parsed = urlparse(entry.data.get(CONF_URL, ""))
                        entry_normalized = f"{entry_parsed.scheme}://{entry_parsed.netloc}{entry_parsed.path.rstrip('/')}"
                        if (
                            entry_normalized == normalized_url
                            and entry.data.get(CONF_USERNAME) == user_input[CONF_USERNAME]
                        ):
                            return self.async_abort(reason="already_configured")

                    if not errors:
                        client = InfometricClient(
                            normalized_url,
                            user_input[CONF_USERNAME],
                            user_input[CONF_PASSWORD],
                        )
                        try:
                            await client.authenticate(
                                aiohttp_client.async_get_clientsession(self.hass)
                            )
                        except Exception as auth_err:  # Differentiate later if needed
                            errors["base"] = "auth_failed"
                        else:
                            user_input[CONF_URL] = normalized_url
                            return self.async_create_entry(
                                title=user_input.get(CONF_NAME, DEFAULT_NAME), data=user_input
                            )
            except Exception:
                errors["base"] = "invalid_url"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_URL, default=f"{DEFAULT_URL}/"): str,
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
                }
            ),
            errors=errors,
        )

    async def async_step_import(self, import_data: dict[str, Any]) -> FlowResult:
        """Handle YAML import (deprecated)."""
        return await self.async_step_user(import_data)
