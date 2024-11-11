"""Example of Selen 2 init."""

# Pymodbus
from berluf_selen_2.modbus_impl.asyncio.timer import (
    Asyncio_timer_factory,
)
from berluf_selen_2.modbus_impl.pymodbus.serial import Pymodbus_serial_intf_factory

# Recuperator
from berluf_selen_2.recup.serial import (
    Recup_serial_intf,
)
from berluf_selen_2.recup import device as recup_device

# Functions
from berluf_selen_2.recup import funcs as recup_funcs

import asyncio


def connect_callb():
    print("Connected")
    return


def disconnect_callb(x: Exception | None):
    print("Disconnected")
    if x != None:
        raise x


async def wait_exit(recup_intf: Recup_serial_intf):
    print(await recup_intf.connect())
    print(recup_intf.get_state())
    print(await recup_intf.wait_state_change())


async def main():
    # Interface for connectiong to serial
    recup_intf = Recup_serial_intf(
        "/dev/pts/2",
        Pymodbus_serial_intf_factory(),
    )
    # Device's memory
    recup = recup_device.Recup_device(recup_intf, None)

    recup.holding_registers.get_single_val(1)

    def bypass_callb(x: bool) -> None:
        print("test")
        return

    bypass = recup_funcs.Bypass(recup, bypass_callb)

    gwc = recup_funcs.GWC(recup)
    gwc.set(False)

    error = recup_funcs.Error(device=recup, timer_factory=Asyncio_timer_factory())

    supply_fan = recup_funcs.Supply_fan(recup, recup_funcs.Fan_non_conv())

    asyncio.ensure_future(wait_exit(recup_intf))

    while True:
        print(error.get())
        print(supply_fan.set(2))
        await asyncio.sleep(2)


asyncio.run(main())
