"""Base Modbus Sensor."""

from dataclasses import dataclass
from functools import cached_property
from typing import Any

from pymodbus.client.mixin import ModbusClientMixin

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import callback

from .coordinator import BaseModbusUpdateCoordinator
from .entity import BaseModbusEntity, SimpleModbusRegisterType


@dataclass(frozen=True)
class SimpleModbusSwitchEntityDescription(SwitchEntityDescription):
    """EntityDescription of a Simple Modbus Switch."""

    modbus_address: int | None = None
    """Modbus register number."""
    modbus_register_type: SimpleModbusRegisterType | None = None
    """Type of data stored in the register."""
    modbus_count: int | None = None
    """Number of registers to read for this sensor."""

    on_value: int = 1
    off_value: int = 0

    @cached_property
    def modbus_registers(self) -> list[int]:
        """Return the Modbus registers."""

        # these must be set, but cannot type them correctly due to
        # "non-default argument 'xyz' follows default argument 'abc'" error
        assert self.modbus_address
        assert self.modbus_register_type

        type_length = self.modbus_register_type.value.value[1]
        modbus_count = self.modbus_count

        if self.modbus_count and type_length and self.modbus_count != type_length:
            raise ValueError(
                "modbus_count does not match the length for this register type"
            )

        if not self.modbus_count:
            if not type_length:
                raise ValueError("modbus_count must be set for this register type")
            modbus_count = type_length

        assert modbus_count is not None

        return list(range(self.modbus_address, self.modbus_address + modbus_count))


class SimpleModbusSwitchEntity(BaseModbusEntity, SwitchEntity):
    """Base class for Modbus sensor entities."""

    entity_description: SimpleModbusSwitchEntityDescription

    def __init__(
        self,
        coordinator: BaseModbusUpdateCoordinator,
        description: SimpleModbusSwitchEntityDescription,
    ):
        """Initialize the Modbus sensor."""
        super().__init__(coordinator, description)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        assert self.entity_description.modbus_register_type

        if self.coordinator.data and all(
            modbus_register in self.coordinator.data
            for modbus_register in self.entity_description.modbus_registers
        ):
            registers = [
                self.coordinator.data[modbus_register]
                for modbus_register in self.entity_description.modbus_registers
            ]
            value = ModbusClientMixin.convert_from_registers(
                registers,
                self.entity_description.modbus_register_type.value,
            )

            if value == self.entity_description.on_value:
                self._attr_is_on = True
            elif value == self.entity_description.off_value:
                self._attr_is_on = False
            else:
                raise ValueError(
                    f"Received unexpected value {value} for switch: only {self.entity_description.on_value} and {self.entity_description.off_value} are supported"
                )
            self._attr_available = True
        else:
            self._attr_available = False
            self._attr_native_value = None

        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the device."""
        assert self.entity_description.modbus_address

        await self.coordinator._modbus_hub.write_register(
            self.entity_description.modbus_address,
            self.entity_description.on_value,
        )
        self.coordinator.data[self.entity_description.modbus_address] = (
            self.entity_description.on_value
        )
        self.coordinator.async_update_listeners()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the device."""
        assert self.entity_description.modbus_address

        await self.coordinator._modbus_hub.write_register(
            self.entity_description.modbus_address,
            self.entity_description.off_value,
        )
        self.coordinator.data[self.entity_description.modbus_address] = (
            self.entity_description.off_value
        )
        self.coordinator.async_update_listeners()
