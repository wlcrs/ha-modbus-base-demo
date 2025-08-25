"""Modbus base component for Home Assistant."""

from .coordinator import BaseModbusUpdateCoordinator
from .modbus import ModbusHub

__all__ = ["BaseModbusUpdateCoordinator", "ModbusHub"]
