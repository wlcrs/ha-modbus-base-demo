"""Config flow for the Modbus Demo integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.modbus_base import ModbusHub
from homeassistant.config_entries import ConfigFlow as BaseConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# TODO adjust the data schema to the data that you need
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT): int,
    }
)

SERIAL_NUMBER_REGISTER = 529
SERIAL_NUMBER_REGISTERS_COUNT = 544 - 529 + 1
SLAVE_ID = 1


class PlaceholderHub(ModbusHub):
    """Placeholder class to make tests pass."""

    async def get_device_serial_number(self) -> str:
        """Get device serial number."""
        serial_number = self._client.convert_from_registers(
            (
                await self._client.read_holding_registers(
                    SERIAL_NUMBER_REGISTER,
                    count=SERIAL_NUMBER_REGISTERS_COUNT,
                    slave=SLAVE_ID,
                )
            ).registers,
            self._client.DATATYPE.STRING,
        )
        assert isinstance(serial_number, str)
        return serial_number


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """

    hub = PlaceholderHub(data[CONF_HOST], data[CONF_PORT])

    if not await hub.connect():
        raise CannotConnect

    # Return info that you want to store in the config entry.
    return {
        "title": "Name of the device",
        "serial_number": await hub.get_device_serial_number(),
    }


class ConfigFlow(BaseConfigFlow, domain=DOMAIN):
    """Handle a config flow for Modbus Demo."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
