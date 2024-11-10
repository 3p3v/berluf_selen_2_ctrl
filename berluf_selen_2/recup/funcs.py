import copy
from enum import Enum
from typing import Callable, override

from ..modbus_slave.validator import (
    Bigger_equal_handler,
    Equal_handler,
    Many_handler,
    One_of_handler,
    Smaller_equal_handler,
)
from ..modbus_slave.observer_func.func import Device_func
from ..modbus_slave.func import (
    Multi_func,
    Common_func,
    Persistant,
    Persistant_executor,
    Timeout_manager,
)
from ..modbus_slave.device import Device
from ..modbus_slave.timer import Timer_factory


class Recup_persistant(Persistant):
    """Specyfies user's setter addresses."""

    def __init__(self, device: Device, impl: Persistant_executor) -> None:
        super().__init__(
            device.holding_registers,
            # Addresses of all options set by the user
            [
                Fan_base._addr_exhaust,
                Fan_base._addr_supply,
                GWC._addr,
                Heater_cooler._addr,
                Binary_switch._addr,
            ],
            impl,
        )


class Unknown_funcs(Device_func):
    """Disable unused values."""

    def __init__(self, device: Device) -> None:
        self._holding_registers_setter = device.holding_registers.get_setter(
            {
                0: [
                    Equal_handler(1),
                    Equal_handler(0),
                    Equal_handler(25),
                    Equal_handler(18),
                    Equal_handler(18),
                    Equal_handler(26),
                    Equal_handler(22),
                    Equal_handler(5),
                    Equal_handler(60),
                    Equal_handler(60),
                    Equal_handler(30),
                ],
                60: [
                    Equal_handler(2),
                    Equal_handler(25),
                    Equal_handler(0),
                    Equal_handler(24),
                ],
                66: [
                    Equal_handler(25),
                    Equal_handler(25),
                    Equal_handler(25),
                ],
                72: [
                    Equal_handler(2),
                ],
                274: [
                    Equal_handler(20),
                ],
                278: [
                    Equal_handler(16),
                ],
            }
        )


# class Recup_mode(Multi_func):
#     _addr = 71

#     class Mode(Enum):
#         Off = 0
#         Max = 1
#         User = 2

#     def __init__(self, device: Device, peristsant: Persistant_executor) -> None:
#         super().__init__(device)
#         self._persistant = peristsant
#         self._holding_registers_setter = self._device.holding_registers.get_setter_unsafe([Supply_fan._addr, Exhaust_fan._addr])
#         loaded_data =

#     @override
#     def callb(self, addr: int, vals: list[int]) -> None:


#     def _save_usr_data(self) -> None:
#         self._persistant.save(
#                     {
#                         self._addr: [self._mode],
#                         Supply_fan._addr: [self._device.holding_registers.get_single_val(Supply_fan._addr)],
#                         Exhaust_fan._addr: [self._device.holding_registers.get_single_val(Exhaust_fan._addr)]
#                     }
#                 )

#     def set(self, mode: Mode) -> None:
#         match mode:
#             case self.Mode.Off:
#                 sf = 0
#                 ef = 0

#                 self._save_usr_data()
#             case self.Mode.Max:
#                 sf = 99
#                 ef = 99

#                 self._save_usr_data()
#             case self.Mode.User:


#         self._holding_registers_setter.set_single_val(Supply_fan._addr, sf, self)
#         self._holding_registers_setter.set_single_val(Exhaust_fan._addr, ef, self)


class Fan_conv:
    """Conversion of fan's speed value."""

    def _from_real_to_conv(self, val: int) -> int:
        """Convert value from registry to display."""
        raise NotImplementedError()

    def _from_conv_to_real(self, val: int) -> int:
        """Convert value from display to registry."""
        raise NotImplementedError()


class Fan_non_conv(Fan_conv):
    """Leaves fan's values as they are displayed in the original panel."""

    @override
    def _from_real_to_conv(self, val: int) -> int:
        return val

    @override
    def _from_conv_to_real(self, val: int) -> int:
        return val


class Fan_linear_conv(Fan_conv):
    """Converts values using linear function."""

    @override
    def _from_real_to_conv(self, val: int) -> int:
        return max(round(1.1 * val - 9.9), 0)

    @override
    def _from_conv_to_real(self, val: int) -> int:
        if val < 0 or val > 99:
            raise ValueError(
                f"Provided value ({val}) is not withon 0 and 99, so it cannot be converted."
            )

        return round(10 / 11 * val + 9)


class Fan_base:  # TODO should exhaust's val be checked?
    """Common entry point for fans that are independent."""

    def __init__(self, conv: Fan_conv):
        self._conv = conv

    _addr_exhaust: int = 70
    _addr_supply: int = 71

    def set(self, val: int) -> None:
        """Set speed in %."""
        self._set(self._conv._from_conv_to_real(val))

    def _set(self, val: int) -> None:
        raise NotImplementedError()

    def get(self) -> int:
        """Get speed in %."""
        return self._conv._from_real_to_conv(self._get())

    def _get(self) -> int:
        """Get speed in %."""
        raise NotImplementedError()


# %%
class Exhaust_fan(Multi_func, Fan_base):
    _addr = Fan_base._addr_exhaust

    def __init__(
        self,
        device: Device,
        conv: Fan_conv,
        usr_callble: Callable[[int, int, int], None] | None = None,
    ) -> None:
        Multi_func.__init__(self, device)
        Fan_base.__init__(self, conv)
        self._usr_callble = usr_callble
        # Set value based on supply
        sup_val = self._device.holding_registers.get_single_val(self._addr_supply)
        self._holding_registers_setter = self._device.holding_registers.get_setter(
            {
                self._addr: [
                    Many_handler(
                        [
                            Bigger_equal_handler(sup_val - 20),
                            Smaller_equal_handler(sup_val),
                        ]
                    )
                ],
            }
        )
        # Set callback to change value when supply or exhaust changes
        self._add_callb(
            self._device.holding_registers,
            self._addr_supply,
            lambda a, vs: self._supply_callb(vs[0]),
        )
        self._add_callb(
            self._device.holding_registers,
            self._addr,
            lambda a, vs: self._exhaust_callb(vs[0]),
        )

    def _get_min_max(self, val: int) -> tuple[int, int]:
        val_min = self._get_min(val)

        return val_min, self._get_max(val)

    def _get_max(self, val: int) -> int:
        return val

    def _get_min(self, val: int) -> int:
        return max(val - 20, 0)

    def _get_val(self, val_min: int, val_max: int) -> int:
        exh_val = self._device.holding_registers.get_single_val(self._addr)
        if exh_val > val_max:
            self._holding_registers_setter.set_single_val(self._addr, val_max)
            exh_val = val_max
        elif exh_val < val_min:
            self._holding_registers_setter.set_single_val(self._addr, val_min)
            exh_val = val_max

        return exh_val

    def _exhaust_callb(self, val: int) -> None:
        (val_min, val_max) = self._get_min_max(
            self._device.holding_registers.get_single_val(self._addr_supply)
        )
        self._usr_callback(
            self._conv._from_real_to_conv(val),
            self._conv._from_real_to_conv(val_min),
            self._conv._from_real_to_conv(val_max),
        )

    def _usr_callback(self, val: int, val_min: int, val_max: int) -> None:
        if self._usr_callble is not None:
            self._usr_callble(val, val_min, val_max)

    def _supply_callb(self, val: int) -> None:
        # Update handler so the exhaust can be only >= supply - 20 || <= supply
        (val_min, val_max) = self._get_min_max(val)
        self._holding_registers_setter.update_handler(
            self._addr,
            Many_handler(
                [Bigger_equal_handler(val_min), Smaller_equal_handler(val_max)]
            ),
        )
        val = self._get_val(val_min, val_max)
        self._holding_registers_setter.set_single_val(self._addr, val)
        self._usr_callback(
            self._conv._from_real_to_conv(val),
            self._conv._from_real_to_conv(val_min),
            self._conv._from_real_to_conv(val_max),
        )

    @override
    def _set(self, val: int) -> None:
        """Set exhaust in %."""
        self._holding_registers_setter.set_single_val(self._addr, val)
        return

    @override
    def _get(self) -> int:
        """Get exhaust in %."""
        return self._device.holding_registers.get_single_val(self._addr)

    def get_max(self) -> int:
        return self._conv._from_real_to_conv(
            self._get_max(
                self._device.holding_registers.get_single_val(self._addr_supply)
            )
        )

    def get_min(self) -> int:
        return self._conv._from_real_to_conv(
            self._get_min(
                self._device.holding_registers.get_single_val(self._addr_supply)
            )
        )


class Supply_fan(Common_func, Fan_base):
    _addr = Fan_base._addr_supply

    def __init__(
        self,
        device: Device,
        conv: Fan_conv,
        usr_callble: Callable[[int], None] | None = None,
    ) -> None:
        Common_func.__init__(self, device, self._addr)
        Fan_base.__init__(self, conv)
        self._usr_callble = usr_callble
        self._holding_registers_setter = self._device.holding_registers.get_setter(
            {
                self._addr: [
                    Many_handler([Bigger_equal_handler(0), Smaller_equal_handler(99)])
                ],
            }
        )

    @override
    def callb(self, addr: int, vals: list[int]) -> None:
        self._usr_callback(self._conv._from_real_to_conv(vals[0]))

    def _usr_callback(self, val: int) -> None:
        if self._usr_callble is not None:
            self._usr_callble(val)

    @override
    def _set(self, val: int) -> None:
        """Set supply in %."""
        # Update value
        self._holding_registers_setter.set_single_val(self._addr, val)

    @override
    def _get(self) -> int:
        """Get supply in %."""
        return self._device.holding_registers.get_single_val(self._addr)


# %%
class GWC(Common_func):
    _addr: int = 64

    def __init__(
        self, device: Device, usr_callble: Callable[[bool], None] | None = None
    ) -> None:
        super().__init__(device, self._addr)
        self._usr_callble = usr_callble
        self._holding_registers_setter = device.holding_registers.get_setter(
            {self._addr: [One_of_handler([0, 1])]}
        )

    @override
    def callb(self, addr: int, vals: list[int]) -> None:
        self._usr_callback(bool(vals[0]))

    def _usr_callback(self, val: bool) -> None:
        if self._usr_callble is not None:
            self._usr_callble(val)

    def set(self, val: bool) -> None:
        """Turn on or off GWC."""
        self._holding_registers_setter.set_single_val(self._addr, int(val))

    def get(self) -> bool:
        return bool(self._device.holding_registers.get_single_val(self._addr))


# %%
class Heater_cooler(Common_func):
    class Mode(Enum):
        Cool = 0
        Heat = 1

    _addr: int = 65

    def __init__(
        self, device: Device, usr_callble: Callable[[Mode], None] | None = None
    ) -> None:
        super().__init__(device, self._addr)
        self._usr_callble = usr_callble
        self._holding_registers_setter = device.holding_registers.get_setter(
            {
                self._addr: [
                    One_of_handler(
                        [Heater_cooler.Mode.Cool.value, Heater_cooler.Mode.Heat.value]
                    )
                ]
            }
        )

    @override
    def callb(self, addr: int, vals: list[int]) -> None:
        self._usr_callback(Heater_cooler.Mode(vals[0]))

    def _usr_callback(self, val: Mode) -> None:
        if self._usr_callble is not None:
            self._usr_callble(val)

    def set(self, val: Mode) -> None:
        """Set heating mode."""
        self._holding_registers_setter.set_single_val(self._addr, val.value)

    def get(self) -> Mode:
        return Heater_cooler.Mode(
            self._device.holding_registers.get_single_val(self._addr)
        )


class Recup_timeout_manager(Timeout_manager):
    def __init__(
        self,
        device: Device,
        timer_factory: Timer_factory,
        reset_callb: Callable[[], None],
        callb: Callable[[], None],
    ):
        super().__init__(
            device.holding_registers,
            timer_factory,
            30,
            reset_callb,
            callb,
        )


# %%
class Error(Multi_func):
    class Error(Enum):
        """All possible errors"""

        P1 = 0
        P2 = 1
        E1 = 2
        E2 = 3
        E3 = 4
        E4 = 5
        E5 = 6
        E6 = 7
        E7 = 8
        E8 = 9

    class Recup_error(Enum):
        """Bits set in registry sent by master"""

        P1 = int("00010000", 2)
        P2 = int("00100000", 2)
        E1 = int("01000000", 2)
        E7 = int("10000000", 2)

    class Visible_error(Enum):
        """Bits set by monitor
        If I checked correctly monitor can only show one option at a time
        """

        OK = int("01110000", 2)
        E1 = int("00110000", 2)
        P1 = int("01100000", 2)
        P2 = int("01010000", 2)
        P1P2 = int(
            "01000000", 2
        )  # Unused, after getting P1 or P2 error, monitor sets one of the codes above; after a while sets to this one

    # Value of temperature registers when error (E2 - E6)
    _EX = int("11111111", 2)

    # Errors on master
    _addr_err: int = 258
    _addr_01: int = 259
    _addr_02: int = 260
    _addr_03: int = 261
    _addr_04: int = 262
    _addr_05: int = 263

    # Error visible on the screen
    _addr_vis: int = 276

    def _set_change_callb_err_helper(self, addr: int, _val: list) -> bool:
        val: int = _val[0]
        ecs = copy.deepcopy(self._ecs)
        rec = Error.Visible_error.OK.value

        if val & Error.Recup_error.P1.value:
            ecs.add(Error.Error.P1)
            rec |= Error.Visible_error.P1.value
        else:
            ecs.discard(Error.Error.P1)

        if val & Error.Recup_error.P2.value:
            ecs.add(Error.Error.P2)
            rec |= Error.Visible_error.P2.value
        else:
            ecs.discard(Error.Error.P2)

        if val & Error.Recup_error.E1.value:
            ecs.add(Error.Error.E1)
            rec |= Error.Visible_error.E1.value
        else:
            ecs.discard(Error.Error.E1)

        if val & Error.Recup_error.E7.value:
            ecs.add(Error.Error.E7)
        else:
            ecs.discard(Error.Error.E7)

        self._holding_registers_setter.set_single_val(self._addr_vis, rec)
        if ecs == self._ecs:
            return False
        else:
            self._ecs = ecs
            return True

    def _set_change_callb_err(self, addr: int, _val: list) -> None:
        """Callbacks run when registry state changes."""
        if self._set_change_callb_err_helper(addr, _val):
            self._usr_callback(list(self._ecs))

    def _set_change_callb_0X_helper(self, val: list, ec: Error) -> bool:
        if val[0] == self._EX:
            self._ecs.add(ec)
            return True
        elif ec in self._ecs:
            self._ecs.remove(ec)
            return True

        return False

    def _set_change_callb_0X(self, val: list, ec: Error) -> None:
        if self._set_change_callb_0X_helper(val, ec):
            self._usr_callback(list(self._ecs))

    def _set_change_callb_01(self, addr: int, val: list) -> None:
        self._set_change_callb_0X(val, Error.Error.E2)

    def _set_change_callb_02(self, addr: int, val: list) -> None:
        self._set_change_callb_0X(val, Error.Error.E3)

    def _set_change_callb_03(self, addr: int, val: list) -> None:
        self._set_change_callb_0X(val, Error.Error.E4)

    def _set_change_callb_04(self, addr: int, val: list) -> None:
        self._set_change_callb_0X(val, Error.Error.E5)

    def _set_change_callb_05(self, addr: int, val: list) -> None:
        self._set_change_callb_0X(val, Error.Error.E6)

    def _timeout_callb(self) -> None:
        if Error.Error.E8 not in self._ecs:
            self._ecs.add(Error.Error.E8)
            self._usr_callback(list(self._ecs))

    def _reset_callb(self) -> None:
        if Error.Error.E8 in self._ecs:
            self._ecs.discard(Error.Error.E8)
            self._usr_callback(list(self._ecs))

    def __init__(
        self,
        device: Device,
        timer_factory: Timer_factory,
        usr_callble: Callable[[list[Error]], None] | None = None,
    ):
        """callb is used when error arises"""
        super().__init__(device)
        self._usr_callble = usr_callble
        self._holding_registers_setter = device.holding_registers.get_setter(
            {
                self._addr_vis: [
                    Many_handler(
                        [
                            Bigger_equal_handler(int("00000000", 2)),
                            Smaller_equal_handler(int("11111111", 2)),
                        ]
                    )
                ]
            }
        )

        self._timer = Recup_timeout_manager(
            device, timer_factory, self._reset_callb, self._timeout_callb
        )
        self._timer.start()

        self._ecs = set()
        self._add_callb(
            self._device.holding_registers, self._addr_err, self._set_change_callb_err
        )
        self._add_callb(
            self._device.holding_registers, self._addr_01, self._set_change_callb_01
        )
        self._add_callb(
            self._device.holding_registers, self._addr_02, self._set_change_callb_02
        )
        self._add_callb(
            self._device.holding_registers, self._addr_03, self._set_change_callb_03
        )
        self._add_callb(
            self._device.holding_registers, self._addr_04, self._set_change_callb_04
        )
        self._add_callb(
            self._device.holding_registers, self._addr_05, self._set_change_callb_05
        )

    def _usr_callback(self, ecs: list[Error]) -> None:
        if self._usr_callble is not None:
            self._usr_callble(ecs)

    def cancel(self) -> None:
        self._timer.cancel()

    def reset(self) -> list:
        """Reset errors on monitor."""
        # Refresh error list
        self._set_change_callb_err_helper(
            self._addr_err,
            [self._device.holding_registers.get_single_val(self._addr_err)],
        )
        for a, e in zip([self._addr_01 ,self._addr_02, self._addr_03, self._addr_04, self._addr_05],  [self.Error.E2, self.Error.E3, self.Error.E4, self.Error.E5, self.Error.E6]):
            self._set_change_callb_0X_helper(
                [self._device.holding_registers.get_single_val(a)],
                e
            )

        return list(self._ecs)

    def get(self) -> list:
        """Get all errors"""
        return list(self._ecs)


class Binary_switch(Common_func):
    """Base binary switch class."""

    _addr: int = 258

    @override
    def callb(self, addr: int, val: list) -> None:
        self._usr_callback(val[0] & self._On)
        return

    def __init__(
        self,
        device: Device,
        on: int,
        usr_callble: Callable[[bool], None] | None = None,
    ) -> None:
        super().__init__(device, self._addr)
        self._On = on  # TODO change to static
        self._device.holding_registers.get_callb_service().add_callb(self._addr, self)
        self._usr_callble = usr_callble

    def _usr_callback(self, val: bool) -> None:
        if self._usr_callble is not None:
            self._usr_callble(val)

    def get(self) -> bool:
        return bool(
            self._device.holding_registers.get_single_val(self._addr) & self._On
        )


class Bypass(Binary_switch):
    def __init__(
        self,
        device: Device,
        usr_callble: Callable[[bool], None] | None = None,
    ) -> None:
        super().__init__(device, int("00001000", 2), usr_callble)


class Heater(Binary_switch):
    def __init__(
        self,
        device: Device,
        usr_callble: Callable[[bool], None] | None = None,
    ) -> None:
        super().__init__(device, int("00000010", 2), usr_callble)


class Pump(Binary_switch):
    def __init__(
        self,
        device: Device,
        usr_callble: Callable[[bool], None] | None = None,
    ) -> None:
        super().__init__(device, int("00000100", 2), usr_callble)


class Thermometer(Common_func):
    """Base thermometer class."""

    _addr: int

    @override
    def callb(self, addr: int, val: list) -> None:
        self._usr_callback(val[0])

    def __init__(
        self,
        device: Device,
        addr: int,
        usr_callble: Callable[[int], None] | None = None,
    ) -> None:
        super().__init__(device, addr)
        self._device.holding_registers.get_callb_service().add_callb(addr, self)
        self._usr_callble = usr_callble

    def _usr_callback(self, val: int) -> None:
        if self._usr_callble is not None:
            self._usr_callble(val)

    def get(self) -> int:
        """Get thermometer value."""
        return self._device.holding_registers.get_single_val(self._addr)


class Thermometer_01(Thermometer):
    _addr: int = 259

    def __init__(
        self, device: Device, usr_callble: Callable[[int], None] | None = None
    ) -> None:
        super().__init__(device, self._addr, usr_callble)


class Thermometer_02(Thermometer):
    _addr: int = 260

    def __init__(
        self, device: Device, usr_callble: Callable[[int], None] | None = None
    ) -> None:
        super().__init__(device, self._addr, usr_callble)


class Thermometer_03(Thermometer):
    _addr: int = 261

    def __init__(
        self, device: Device, usr_callble: Callable[[int], None] | None = None
    ) -> None:
        super().__init__(device, self._addr, usr_callble)


class Thermometer_04(Thermometer):
    _addr: int = 262

    def __init__(
        self, device: Device, usr_callble: Callable[[int], None] | None = None
    ) -> None:
        super().__init__(device, self._addr, usr_callble)


class Thermometer_05(Thermometer):
    _addr: int = 263

    def __init__(
        self, device: Device, usr_callble: Callable[[int], None] | None = None
    ) -> None:
        super().__init__(device, self._addr, usr_callble)
