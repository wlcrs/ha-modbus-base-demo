"""Base Modbus Sensor."""

from dataclasses import dataclass
from functools import cached_property

from pymodbus.client.mixin import ModbusClientMixin

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.core import callback

from .coordinator import BaseModbusUpdateCoordinator
from .entity import BaseModbusEntity, SimpleModbusRegisterType


@dataclass(frozen=True)
class SimpleModbusSensorEntityDescription(SensorEntityDescription):
    """EntityDescription of a Simple Modbus sensor."""

    modbus_address: int | None = None
    """Modbus register number."""
    modbus_register_type: SimpleModbusRegisterType | None = None
    """Type of data stored in the register."""
    modbus_count: int | None = None
    """Number of registers to read for this sensor."""

    scale: float | None = None
    """When set, the value returned by the device will be divided by this scale."""

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


class SimpleModbusSensorEntity(BaseModbusEntity, SensorEntity):
    """Base class for Modbus sensor entities."""

    entity_description: SimpleModbusSensorEntityDescription

    def __init__(
        self,
        coordinator: BaseModbusUpdateCoordinator,
        description: SimpleModbusSensorEntityDescription,
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

            if self.entity_description.scale is not None:
                assert isinstance(value, (int, float)), (
                    "Scale can only be set for registers containing a number"
                )
                value = value / self.entity_description.scale
            self._attr_native_value = value  # type: ignore[reportAccessAttributeIssue]
            self._attr_available = True
        else:
            self._attr_available = False
            self._attr_native_value = None

        self.async_write_ha_state()
