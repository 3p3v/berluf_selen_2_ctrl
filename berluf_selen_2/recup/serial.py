from typing import Tuple, override

from ..modbus_slave.validator import Setter_validator
from ..modbus_slave.intf import Device_buildable_intf, Device_async_intf
from ..modbus_slave.serial import Serial_conf, Device_serial_intf_factory
from ..modbus_slave.memory import Memory_rw
from ..modbus_slave.observer_func.callb import Callb_store, Invoke_callb_store


class Recup_serial_intf(Device_buildable_intf):  # TODO
    """Sets up an interface for the recuperator"""

    def __init__(
        self,
        com: str,
        impl_builder: Device_serial_intf_factory,
    ):
        self._impl = impl_builder.create_intf(Serial_conf(com, 9600, 1, 8, "N")) # Has to be odd
        return

    @override
    def create_coils(
        self,
        mem: dict[int, list[int]],
        setter_validator: Setter_validator,
        setter_validator_master: Setter_validator,
        callbs: Callb_store,
        invokable_callbs: Invoke_callb_store,
    ) -> None:
        self._coils = self._impl.create_coils(
            mem, setter_validator, setter_validator_master, callbs, invokable_callbs
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
        self._discrete_inputs = self._impl.create_discrete_inputs(
            mem, setter_validator, setter_validator_master, callbs, invokable_callbs
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
        self._holding_registers = self._impl.create_holding_registers(
            mem, setter_validator, setter_validator_master, callbs, invokable_callbs
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
        self._input_registers = self._impl.create_input_registers(
            mem, setter_validator, setter_validator_master, callbs, invokable_callbs
        )

    @override
    def create_slave(self) -> Tuple[Memory_rw, Memory_rw, Memory_rw, Memory_rw]:
        return self._impl.create_slave()

    @override
    async def connect(self) -> Device_async_intf.State:
        return await self._impl.connect()

    @override
    async def disconnect(self) -> None:
        return await self._impl.disconnect()
    
    @override
    def get_state(self) -> Device_async_intf.State:
        return self._impl.get_state()
