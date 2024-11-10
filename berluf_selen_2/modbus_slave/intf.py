from enum import Enum

from .observer_func.callb import (
    Callb_store,
    Invoke_callb_store,
)
from .validator import (
    Setter_validator,
)
from .memory import Memory_rw


class Slave_builder:
    """Base class for creating and adding slaves to the interface."""

    def _reset_memories(self) -> None:
        self._coils = self.create_coils(
            {},
            Setter_validator([]),
            Setter_validator([]),
            Callb_store(),
            Invoke_callb_store(),
        )
        self._discrete_inputs = self.create_discrete_inputs(
            {},
            Setter_validator([]),
            Setter_validator([]),
            Callb_store(),
            Invoke_callb_store(),
        )
        self._holding_registers = self.create_holding_registers(
            {},
            Setter_validator([]),
            Setter_validator([]),
            Callb_store(),
            Invoke_callb_store(),
        )
        self._input_registers = self.create_input_registers(
            {},
            Setter_validator([]),
            Setter_validator([]),
            Callb_store(),
            Invoke_callb_store(),
        )

    def create_coils(
        self,
        mem: dict[int, list[int]],
        setter_validator: Setter_validator,
        setter_validator_master: Setter_validator,
        callbs: Callb_store,
        invokable_callbs: Invoke_callb_store,
    ) -> None:
        """Create 'coils' memory."""
        raise NotImplementedError()

    def create_discrete_inputs(
        self,
        mem: dict[int, list[int]],
        setter_validator: Setter_validator,
        setter_validator_master: Setter_validator,
        callbs: Callb_store,
        invokable_callbs: Invoke_callb_store,
    ) -> None:
        """Create 'discrete inputs' memory."""
        raise NotImplementedError()

    def create_holding_registers(
        self,
        mem: dict[int, list[int]],
        setter_validator: Setter_validator,
        setter_validator_master: Setter_validator,
        callbs: Callb_store,
        invokable_callbs: Invoke_callb_store,
    ) -> None:
        """Create 'holding registers' memory."""
        raise NotImplementedError()

    def create_input_registers(
        self,
        mem: dict[int, list[int]],
        setter_validator: Setter_validator,
        setter_validator_master: Setter_validator,
        callbs: Callb_store,
        invokable_callbs: Invoke_callb_store,
    ) -> None:
        """Create 'input registers' memory."""
        raise NotImplementedError()

    def create_slave(self) -> tuple[Memory_rw, Memory_rw, Memory_rw, Memory_rw]:
        """Create the slave device."""
        raise NotImplementedError()


class Device_async_intf:
    """Base for modbus device connectivity interface."""
    
    class State(Enum):
        """Reason why connection ended."""
        NOT_CONNECTED = 0
        CONNECTING = 1
        CONNECTED = 2
        DISCONNECTED = 3
        CONNECTION_ERROR = 4
        STARTUP_ERROR = 5
        INNER_ERROR = 6

    async def connect(self) -> State:
        """Connect to the interface."""
        raise NotImplementedError()

    async def disconnect(self) -> None:
        """Disconnect from the interface."""
        raise NotImplementedError()
    
    def get_state(self) -> State:
        raise NotImplementedError()


class Device_buildable_intf(Slave_builder, Device_async_intf):
    """Slave_builder and Device_async_intf combined for convinience."""

