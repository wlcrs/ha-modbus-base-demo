"""The Modbus Demo integration."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from pymodbus.client import AsyncModbusTcpClient

from homeassistant.components.modbus_base import BaseModbusUpdateCoordinator, ModbusHub
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import UPDATE_INTERVAL

_PLATFORMS: list[Platform] = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


@dataclass
class ModbusDemoConfigEntryData:
    """Modbus Demo config entry runtime data."""

    client: AsyncModbusTcpClient
    coordinator: BaseModbusUpdateCoordinator


type ModbusDemoConfigEntry = ConfigEntry[ModbusDemoConfigEntryData]


async def async_setup_entry(hass: HomeAssistant, entry: ModbusDemoConfigEntry) -> bool:
    """Set up Modbus Demo from a config entry."""

    client = AsyncModbusTcpClient(entry.data[CONF_HOST], port=entry.data[CONF_PORT])

    if not await client.connect():
        raise ConfigEntryNotReady("Could not connect to the Modbus device")

    _LOGGER.debug(
        "Connected to the Modbus device at %s:%s",
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
    )
    hub = ModbusHub(hass, client)
    entry.runtime_data = ModbusDemoConfigEntryData(
        client=client,
        coordinator=BaseModbusUpdateCoordinator(
            hass, _LOGGER, hub, "Demo", UPDATE_INTERVAL
        ),
    )

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ModbusDemoConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, _PLATFORMS):
        entry.runtime_data.client.close()

    return unload_ok
