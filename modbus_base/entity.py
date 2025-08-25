"""Base Modbus Entity."""

from dataclasses import dataclass
from enum import Enum
from functools import cached_property

from pymodbus.client.mixin import ModbusClientMixin

from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import MODBUS_REGISTERS
from .coordinator import BaseModbusUpdateCoordinator

PyModbusDataType = ModbusClientMixin.DATATYPE


class SimpleModbusRegisterType(Enum):
    """Enum for the Modbus register type."""

    INT16 = PyModbusDataType.INT16
    UINT16 = PyModbusDataType.UINT16
    INT32 = PyModbusDataType.INT32
    UINT32 = PyModbusDataType.UINT32
    INT64 = PyModbusDataType.INT64
    UINT64 = PyModbusDataType.UINT64
    FLOAT32 = PyModbusDataType.FLOAT32
    FLOAT64 = PyModbusDataType.FLOAT64
    STRING = PyModbusDataType.STRING
    BITS = PyModbusDataType.BITS


@dataclass(frozen=True)
class SimpleModbusEntityDescription:
    """Entity description for a simple Modbus entity."""

    modbus_address: int | None = None
    modbus_register_type: SimpleModbusRegisterType | None = None
    modbus_count: int | None = None

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


class BaseModbusEntity(CoordinatorEntity[BaseModbusUpdateCoordinator]):
    """Base Modbus Entity."""

    def __init__(
        self,
        coordinator: BaseModbusUpdateCoordinator,
        description: EntityDescription,
    ) -> None:
        """Initialize the entity."""
        super().__init__(
            coordinator,
            context={
                MODBUS_REGISTERS: description.modbus_registers,  # type: ignore[reportAccessAttributeIssue]
            },
        )
        self.entity_description = description
