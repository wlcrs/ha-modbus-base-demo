"""Demo Modbus sensors."""

from __future__ import annotations

import logging

from homeassistant.components.modbus_base.sensor import (
    SimpleModbusRegisterType,
    SimpleModbusSensorEntity,
    SimpleModbusSensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ModbusDemoConfigEntry

_LOGGER = logging.getLogger(__name__)

SENSORS: list[SimpleModbusSensorEntityDescription] = [
    SimpleModbusSensorEntityDescription(
        key="sensor_1",
        name="UInt16 Sensor",
        modbus_address=2168,
        modbus_register_type=SimpleModbusRegisterType.UINT16,
    ),
    SimpleModbusSensorEntityDescription(
        key="sensor_2",
        name="Float32 Sensor",
        modbus_address=4688,
        modbus_register_type=SimpleModbusRegisterType.INT16,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ModbusDemoConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Demo sensors from config entry."""
    _LOGGER.debug(
        "Set up sensor for entry_id %s",
        config_entry.entry_id,
    )

    for sensor in SENSORS:
        async_add_entities(
            [SimpleModbusSensorEntity(config_entry.runtime_data.coordinator, sensor)],
            True,
        )
