"""Config flow for ClubLog HA Bridge integration."""

from __future__ import annotations

import logging
import re
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import (
    CONF_API_KEY,
    CONF_APP_PASSWORD,
    CONF_CALLSIGN,
    CONF_EMAIL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

CALLSIGN_REGEX = re.compile(r"^[A-Z0-9]{1,3}[0-9][A-Z0-9]{0,4}$", re.IGNORECASE)


class ClubLogConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ClubLog."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            callsign = user_input.get(CONF_CALLSIGN, "").strip().upper()

            if not CALLSIGN_REGEX.match(callsign):
                errors["base"] = "invalid_callsign"
            elif not user_input.get(CONF_API_KEY):
                errors["base"] = "api_key_required"
            elif not user_input.get(CONF_EMAIL):
                errors["base"] = "email_required"
            elif not user_input.get(CONF_APP_PASSWORD):
                errors["base"] = "app_password_required"
            else:
                await self.async_set_unique_id(callsign)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"ClubLog ({callsign})",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CALLSIGN): str,
                    vol.Required(CONF_API_KEY): str,
                    vol.Required(CONF_EMAIL): str,
                    vol.Required(CONF_APP_PASSWORD): str,
                }
            ),
            errors=errors,
        )

