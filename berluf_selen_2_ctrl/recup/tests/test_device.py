"""Recuperator device tests."""

import pytest

from ...modbus_slave.tests.dummies import (
    Dummy_serial_intf_factory,
)

from ..serial import Recup_serial_intf

from ..device import Recup_device


class Test_recup_device:
    # Loaded registry from some previous session
    data: dict[int, list[int]] = {
        0: list(range(0, 11)),
        60: list(range(0, 13)),
        258: list(range(0, 6)),
        274: list(range(0, 5)),
    }

    def create_recup_device(self) -> Recup_device:
        return Recup_device(Recup_serial_intf("COM5", Dummy_serial_intf_factory()))

    def create_recup_device_with_persistant(self) -> Recup_device:
        return Recup_device(
            Recup_serial_intf("COM5", Dummy_serial_intf_factory()),
            self.data,
        )

    def test_init_default(self):
        """Initialize the device using default arguments."""
        device = self.create_recup_device()
        # Check if memory pattern ok
        mem = device.holding_registers.get_all_multi_vals()
        for a, l in [(a, len(vs)) for a, vs in self.data.items()]:
            assert len(mem[a]) == l

    def test_init_with_persistant(self):
        """Initialize the device using loaded persistant data."""
        device = self.create_recup_device_with_persistant()
        assert sorted(device.holding_registers.get_all_multi_vals().items()) == sorted(
            self.data.items()
        )
