"""Support for Modbus."""

from __future__ import annotations

import asyncio
from collections.abc import Iterable
import logging
import time

from pymodbus.client.base import ModbusBaseClient

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

MAX_BATCHED_REGISTERS_COUNT = 64
MAX_BATCHED_REGISTERS_GAP = 1


class ModbusHub:
    """Thread safe wrapper class for pymodbus."""

    _client: ModbusBaseClient
    _msg_wait: float | None = None

    __last_call_finished_at: float | None = None

    def __init__(
        self,
        hass: HomeAssistant,
        client: ModbusBaseClient,
        _msg_wait: float | None = None,
    ) -> None:
        """Initialize the Modbus hub."""

        # generic configuration
        self._client = client
        self._msg_wait = _msg_wait
        self._lock = asyncio.Lock()
        self.hass = hass

    async def connect(self) -> bool:
        """Connect client."""
        async with self._lock:
            return await self._client.connect()

    async def cooldown_between_modbus_calls(self) -> None:
        """Cooldown between Modbus calls."""
        if self._msg_wait is not None and self.__last_call_finished_at is not None:
            cooldown_time_needed = (
                self.__last_call_finished_at + self._msg_wait
            ) - time.time()

            if cooldown_time_needed > 0:
                _LOGGER.debug(
                    "Sleeping for %s seconds before making next call",
                    cooldown_time_needed,
                )
                await asyncio.sleep(cooldown_time_needed)

    async def batch_read(
        self,
        registers: Iterable[int],
        slave: int = 1,
    ) -> dict[int, int]:
        """Read multiple registers."""

        sorted_registers = sorted(registers)

        async with self._lock:
            if not self._client:
                return {}

            result = {}

            batch_first_idx = 0
            batch_last_idx = 0

            while batch_first_idx < len(sorted_registers):
                # Batch together registers:
                while (
                    batch_last_idx + 1 < len(sorted_registers)
                    and
                    # as long as the total amount of registers doesn't exceed MAX_BATCHED_REGISTERS_COUNT
                    (
                        sorted_registers[batch_last_idx + 1]
                        - sorted_registers[batch_first_idx]
                        < MAX_BATCHED_REGISTERS_COUNT
                    )
                    and
                    # as long as the gap between registers is not more than MAX_BATCHED_REGISTERS_GAP
                    (
                        sorted_registers[batch_last_idx + 1]
                        - sorted_registers[batch_last_idx]
                        <= MAX_BATCHED_REGISTERS_GAP
                    )
                ):
                    batch_last_idx += 1

                registers_count = (
                    sorted_registers[batch_last_idx]
                    - sorted_registers[batch_first_idx]
                    + 1
                )

                await self.cooldown_between_modbus_calls()
                response = await self._client.read_holding_registers(
                    sorted_registers[batch_first_idx],
                    count=registers_count,
                    slave=slave,
                )
                self.__last_call_finished_at = time.time()

                if response.isError():
                    _LOGGER.error(
                        "Read error while reading register %d with count %d: %s",
                        sorted_registers[batch_first_idx],
                        registers_count,
                        response,
                    )
                    return {}

                for idx in range(batch_first_idx, batch_last_idx + 1):
                    result[sorted_registers[idx]] = response.registers[
                        sorted_registers[idx] - sorted_registers[batch_first_idx]
                    ]

                batch_first_idx = batch_last_idx + 1
                batch_last_idx = batch_first_idx

            return result

    async def write_register(self, register: int, value: int, slave: int = 1) -> None:
        """Write a single register."""
        async with self._lock:
            await self.cooldown_between_modbus_calls()

            await self._client.write_register(register, value, slave=slave)
            self.__last_call_finished_at = time.time()
