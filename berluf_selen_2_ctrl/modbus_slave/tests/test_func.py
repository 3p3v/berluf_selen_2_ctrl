"""Memory observer tests."""

from typing import Callable
import pytest

from ..memory import (
    Memory,
)

from ..observer_func.callb import Callb_store, Invoke_callb_store
from .dummies import (
    Dummy_memory_rw,
)
from ..validator import Setter_validator, Setter_any_validator

from ..device import Device
from ..func import Multi_func


class Dummy_multi_func(Multi_func):
    def __init__(self, device: Device) -> None:
        super().__init__(device)

    def add_callb(
        self, memory: Memory, addr: int, func: Callable[[int, list[int]], None]
    ) -> None:
        return super()._add_callb(memory, addr, func)

    def get_device(self) -> Device:
        return self._device


class Test_multi_func:
    """Multi callback function tests."""

    @pytest.fixture
    def fixt(self) -> Dummy_multi_func:
        mem = Dummy_memory_rw(
            {},
            # Validation from functions' side
            Setter_validator([]),
            # Validation from masters' side
            Setter_any_validator(),
            # Callbacks corresponding to particular addresses
            Callb_store(),
            # Invoking observers after any action from master
            Invoke_callb_store(),
        )

        self.device = Device(
            mem,
            mem,
            mem,
            mem,
        )
        return Dummy_multi_func(self.device)

    def test_run_callb(self, fixt: Dummy_multi_func):
        res = {1: [], 2: []}

        def set_val(res: list[int], addr: int, vals: list) -> None:
            res.extend(vals)

        fixt.add_callb(
            fixt.get_device().holding_registers, 1, lambda a, v: set_val(res[1], a, v)
        )
        fixt.add_callb(
            fixt.get_device().holding_registers, 2, lambda a, v: set_val(res[2], a, v)
        )

        input = {1: [3, 7, 100], 2: [9, 6, 256]}
        device = fixt.get_device()
        for k, vs in input.items():
            for v in vs:
                device.holding_registers.set_single_val_ext(k, v)

        for k, vs in input.items():
            for v in vs:
                assert v in res[k]
