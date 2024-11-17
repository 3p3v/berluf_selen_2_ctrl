"""Dummy test objects."""

from typing import Callable, override

from ..serial import (
    Device_serial_intf_factory,
    Serial_conf,
)

from ..observer_func.callb import Callb_store, Invoke_callb_store
from ..func import Invokable_func, Observer_func
from ..intf import Device_buildable_intf
from ..memory import Memory_rw
from ..validator import Setter_validator
from ..timer import Timer, Timer_factory


class Dummy_observer_func(Observer_func):
    """Address observer dummy for testing."""

    def __init__(self, addrs: list[int], store: Callb_store) -> None:
        super().__init__()
        self.results: dict[int, int | None] = {}
        for a in addrs:
            self.results[a] = None

        store.add_callb_per_addr(addrs, self)

    @override
    def callb(self, addr: int, vals: list[int]) -> None:
        for a, v in zip(range(addr, addr + len(vals)), vals):
            self.results[a] = v


class Dummy_invokable_func(Invokable_func):
    """Dummy invokable observer for testing."""

    def __init__(self, store: Invoke_callb_store):
        super().__init__()
        self.result = False
        store.add_callb(self)

    @override
    def callb(self) -> None:
        self.result = True


class Dummy_memory_rw(Memory_rw):
    """Dummy memory for testing."""

    def __init__(
        self,
        mem: dict[int, list[int]],
        # Validation from functions' side
        setter_validator: Setter_validator,
        # Validation from masters' side
        master_setter_validator: Setter_validator,
        # Callbacks corresponding to particular addresses
        callbs: Callb_store,
        # Invoking observers after any action from master
        invoke_callbs: Invoke_callb_store,
    ):
        super().__init__(
            setter_validator,
            master_setter_validator,
            callbs,
            invoke_callbs,
        )
        self.values: dict[int, int] = {}

        for addr, vs in mem.items():
            for a, v in zip(range(addr, addr + len(vs)), vs):
                if self.values.get(a) is None:
                    self.values[a] = v
                    continue

                raise RuntimeError(f"Address {a} specyfied many times.")

    # Internal
    @override
    def get_address_list(self) -> list[int]:
        return list(self.values.keys())

    @override
    def _get_single_val(self, addr: int) -> int:
        return self.values[addr]

    @override
    def _get_multi_val(self, addr: int, count: int) -> list[int]:
        return [self.values[a] for a in range(addr, addr + count)]

    @override
    def _set_single_val(self, addr: int, val: int) -> None:
        self.values[addr] = val

    @override
    def _set_multi_val(self, addr: int, val: list) -> None:
        for a, v in zip(range(addr, addr + len(val)), val):
            self.values[a] = v

    @override
    def get_all_single_vals(self) -> dict[int, int]:
        return self.values

    # External interface for testing
    def set_multi_val_ext(self, addr: int, vals: list[int]) -> None:
        """Set the requested values of the datastore."""
        self._master_setter_validator.validate_vals(addr, vals)
        for a, v in zip(range(addr, addr + len(vals)), vals):
            self.values[a] = v
        # Run callbacks
        self._invoke_callbs.run_callbs()
        self._callbs.run_callbs(addr, vals)

    def set_single_val_ext(self, addr: int, val: int) -> None:
        self.set_multi_val_ext(addr, [val])

    def get_multi_val_ext(self, addr: int, count: int = 1) -> list[int]:
        """Set the requested values of the datastore."""
        # self._master_validator.validate(addr, count)
        self._invoke_callbs.run_callbs()
        return [self.values[a] for a in range(addr, addr + count)]


class Dummy_intf(Device_buildable_intf):
    def __init__(self) -> None:
        super().__init__()
        self._reset_memories()

    def _create_memory(
        self,
        mem: dict[int, list[int]],
        setter_validator: Setter_validator,
        setter_validator_master: Setter_validator,
        callbs: Callb_store,
        invokable_callbs: Invoke_callb_store,
    ) -> Dummy_memory_rw:
        return Dummy_memory_rw(
            mem,
            setter_validator,
            setter_validator_master,
            callbs,
            invokable_callbs,
        )

    @override
    def create_coils(
        self,
        mem: dict[int, list[int]],
        setter_validator: Setter_validator,
        setter_validator_master: Setter_validator,
        callbs: Callb_store,
        invokable_callbs: Invoke_callb_store,
    ) -> None:
        self._coils = self._create_memory(
            mem,
            setter_validator,
            setter_validator_master,
            callbs,
            invokable_callbs,
        )

    @override
    def create_discrete_inputs(
        self,
        mem: dict[int, list[int]],
        setter_validator: Setter_validator,
        setter_validator_master: Setter_validator,
        callbs: Callb_store,
        invokable_callbs: Invoke_callb_store,
    ) -> None:
        self._discrete_inputs = self._create_memory(
            mem,
            setter_validator,
            setter_validator_master,
            callbs,
            invokable_callbs,
        )

    @override
    def create_holding_registers(
        self,
        mem: dict[int, list[int]],
        setter_validator: Setter_validator,
        setter_validator_master: Setter_validator,
        callbs: Callb_store,
        invokable_callbs: Invoke_callb_store,
    ) -> None:
        self._holding_registers = self._create_memory(
            mem,
            setter_validator,
            setter_validator_master,
            callbs,
            invokable_callbs,
        )

    @override
    def create_input_registers(
        self,
        mem: dict[int, list[int]],
        setter_validator: Setter_validator,
        setter_validator_master: Setter_validator,
        callbs: Callb_store,
        invokable_callbs: Invoke_callb_store,
    ) -> None:
        self._input_registers = self._create_memory(
            mem,
            setter_validator,
            setter_validator_master,
            callbs,
            invokable_callbs,
        )

    @override
    def create_slave(self) -> tuple[Memory_rw, Memory_rw, Memory_rw, Memory_rw]:
        """Create the slave device."""
        _discrete_inputs = self._discrete_inputs
        _coils = self._coils
        _input_registers = self._input_registers
        _holding_registers = self._holding_registers

        return (
            _coils,
            _discrete_inputs,
            _holding_registers,
            _input_registers,
        )

    @override
    async def connect(self) -> None:
        """Connect to the interface."""
        return

    @override
    async def disconnect(self) -> None:
        """Disconnect from the interface."""
        return


class Dummy_serial_intf_factory(Device_serial_intf_factory):
    @override
    def create_intf(
        self,
        conf: Serial_conf,
    ) -> Device_buildable_intf:
        return Dummy_intf()


class Dummy_timer(Timer):
    def __init__(self, callb: Callable[[], None]):
        super().__init__()
        self._callb = callb

    @override
    def start(self) -> None:
        pass

    @override
    def cancel(self) -> None:
        pass

    def fire(self) -> None:
        self._callb()


class Dummy_timer_factory(Timer_factory):
    def __init__(self):
        super().__init__()
        self._timers: list[Dummy_timer] = []

    @override
    def create_timer(self, timeout: int, callb: Callable[[], None]) -> Timer:
        t = Dummy_timer(callb)
        self._timers.append(t)
        return t

    def get_last_timer(self):
        return self._timers[-1]
