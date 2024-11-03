"""Memorie's base function classes and base functions."""

from typing import Callable, override

from .observer_func.func import Observer_func, Invokable_func
from .device import Device
from .memory import Memory
from .timer import Timer_factory


class Common_func(Observer_func):
    """Base function for funcs observing particular address."""

    def __init__(self, device: Device, self_addr: int) -> None:
        self._device = device
        self._device.holding_registers.get_callb_service().add_callb(self_addr, self)


class Multi_func(Observer_func):
    """Function that uses multiple addresses."""

    def __init__(self, device: Device) -> None:
        self._device = device
        self._callbs: dict[int, Callable[[int, list[int]], None]] = {}

    def _add_callb(
        self, memory: Memory, addr: int, func: Callable[[int, list[int]], None]
    ) -> None:
        if self._callbs.get(addr) is None:
            memory.get_callb_service().add_callb(addr, self)
            self._callbs[addr] = func
        else:
            raise RuntimeError(f"Callback already supplied for the address {addr}.")

    @override
    def callb(self, addr: int, vals: list[int]) -> None:
        self._callbs[addr](addr, vals)


class Timeout_manager(Invokable_func):
    """Checks if connection between master and slave is active."""

    def __init__(
        self,
        memory: Memory,
        timer_factory: Timer_factory,
        timeout: int,
        reset_callb: Callable[[], None],
        callb: Callable[[], None],
    ):
        self._usr_callb = callb
        self._usr_reset_callb = reset_callb
        self._timer = timer_factory.create_timer(timeout, self._fail_callb)
        memory.get_invoke_callb_service().add_callb(self)

    @override
    def callb(self) -> None:
        self._timer.cancel()
        self._usr_reset_callb()
        self._timer.start()

    def _fail_callb(self) -> None:
        self._usr_callb()
        self._timer.start()

    def start(self) -> None:
        """Start timeout manager."""
        self._timer.start()

    def cancel(self) -> None:
        """Stop timeout manager."""
        self._timer.cancel()


# TODO make next timeout manager that checks bool for activity every second


class Persistant_executor:
    """Base class for saving implementation."""

    def save(self, mem: dict[int, list[int]]) -> None:
        """Save specyfied data addresses."""
        raise NotImplementedError()


class Persistant(Observer_func):
    """Base class for any device's persistant data."""

    def __init__(
        self,
        memory: Memory,
        addrs: list[int],
        impl: Persistant_executor,
    ) -> None:
        self._impl = impl
        self._memory = memory
        self._memory.get_callb_service().add_callb_per_addr(addrs, self)

    @override
    def callb(self, addr: int, vals: list[int]) -> None:
        self._impl.save(self._memory.get_all_multi_vals())
