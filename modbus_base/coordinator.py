"""Base Modbus DataUpdateCoordinator."""

from datetime import timedelta
from itertools import chain
import logging
from typing import Any

from pymodbus.exceptions import ModbusException

from homeassistant.core import HomeAssistant
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import MODBUS_REGISTERS
from .modbus import ModbusHub

_LOGGER = logging.getLogger(__name__)


class BaseModbusUpdateCoordinator(DataUpdateCoordinator[dict[int, Any]]):
    """A specialised DataUpdateCoordinator for Huawei Solar entities."""

    _modbus_hub: ModbusHub

    def __init__(
        self,
        hass: HomeAssistant,
        logger: logging.Logger,
        modbus_hub: ModbusHub,
        name: str,
        update_interval: timedelta | None = None,
        request_refresh_debouncer: Debouncer | None = None,
    ) -> None:
        """Create a HuaweiSolarUpdateCoordinator."""
        super().__init__(
            hass,
            logger,
            name=name,
            update_interval=update_interval,
            update_method=None,
            request_refresh_debouncer=request_refresh_debouncer,
        )
        self._modbus_hub = modbus_hub

    async def _async_update_data(self):
        modbus_registers = set(
            chain.from_iterable(ctx[MODBUS_REGISTERS] for ctx in self.async_contexts())
        )
        if not len(modbus_registers):
            _LOGGER.debug("No Modbus registers to update")

        try:
            return await self._modbus_hub.batch_read(modbus_registers)
        except ModbusException as err:
            raise UpdateFailed(f"Could not update values: {err}") from err
