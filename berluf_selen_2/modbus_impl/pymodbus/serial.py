from ...modbus_slave.observer_func.callb import (
    Callb_store,
    Invoke_callb_store,
)
from ...modbus_slave.validator import Setter_validator
from ...modbus_slave.intf import Device_buildable_intf, Device_async_intf
from ...modbus_slave.serial import Serial_conf, Device_serial_intf_factory
from .memory import Pymodbus_memory
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.server import ModbusSerialServer

import asyncio
from asyncio import Event
from typing import Callable, override


class Pymodbus_intf(Device_buildable_intf):
    def __init__(self) -> None:
        super().__init__()
        self._store: dict = {}
        self._i = 1
        self._reset_memories()

    def _create_memory(
        self,
        mem: dict[int, list[int]],
        setter_validator: Setter_validator,
        setter_validator_master: Setter_validator,
        callbs: Callb_store,
        invokable_callbs: Invoke_callb_store,
    ) -> Pymodbus_memory:
        return Pymodbus_memory(
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
    def create_slave(self) -> tuple:
        _discrete_inputs = self._discrete_inputs
        _coils = self._coils
        _input_registers = self._input_registers
        _holding_registers = self._holding_registers
        self._reset_memories()
        self._store[self._i] = ModbusSlaveContext(
            di=_discrete_inputs,
            co=_coils,
            ir=_input_registers,
            hr=_holding_registers,
            zero_mode=True,
        )  # TODO Follow mems pattern

        self._i += 1

        return (
            _coils,
            _discrete_inputs,
            _holding_registers,
            _input_registers,
        )


class Pymodbus_serial_server(ModbusSerialServer):
    """Imlementation of serial modbus connection."""
    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._state = Device_async_intf.State.NOT_CONNECTED
        
    @override
    def callback_connected(self) -> None:
        self._state = Device_async_intf.State.CONNECTED
        
    @override
    def callback_disconnected(self, exc: Exception | None) -> None:
        super().callback_disconnected(exc=exc)
        if exc is None:
            self._state = Device_async_intf.State.DISCONNECTED
        else:
            self._state = Device_async_intf.State.CONNECTION_ERROR
            
    @override
    def callback_inner_error(self, exc: Exception) -> None:
        super().callback_inner_error(exc=exc)
        self._state = Device_async_intf.State.INNER_ERROR

    async def run_connect(self) -> None:
        if self._state in (Device_async_intf.State.CONNECTING, Device_async_intf.State.CONNECTED):
            return
            
        self._state = Device_async_intf.State.CONNECTING
        await self.serve_forever()
        if self.serving.result() == False and self._state == Device_async_intf.State.CONNECTING:
            self._state = Device_async_intf.State.STARTUP_ERROR
        

    async def run_disconnect(self) -> None:
        return await self.shutdown()
    
    def get_state(self) -> Device_async_intf.State:
        return self._state


class Pymodbus_serial_intf(Pymodbus_intf):
    def __init__(
        self,
        conf: Serial_conf = Serial_conf(),
    ):
        super().__init__()
        self._conf = conf
        self._server: Pymodbus_serial_server | None = None

    @override
    async def connect(self) -> None:
        self._context = ModbusServerContext(slaves=self._store, single=False)
        self._server = Pymodbus_serial_server(
            context=self._context,  # Data storage
            port=self._conf.com,  # serial port
            stopbits=self._conf.stop_bits,  # The number of stop bits to use
            bytesize=self._conf.char_size,  # The bytesize of the serial messages
            parity=self._conf.parity,  # Which kind of parity to use
            baudrate=self._conf.baud_rate,  # The baud rate to use for the serial device
        )
        await self._server.run_connect()

    @override
    async def disconnect(self) -> None:
        if self._server is not None:
            await self._server.run_disconnect()
            
    @override
    def get_state(self) -> Device_async_intf.State:
        if self._server is not None:
            return self._server.get_state()
        
        return Device_async_intf.State.NOT_CONNECTED


class Pymodbus_serial_intf_factory(Device_serial_intf_factory):
    def create_intf(
        self,
        conf: Serial_conf,
    ) -> Device_buildable_intf:
        return Pymodbus_serial_intf(conf)
