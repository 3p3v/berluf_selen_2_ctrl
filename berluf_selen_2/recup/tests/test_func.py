"""Recuperator functions' tests."""

import pytest

from ...modbus_slave.observer_func.func import Device_func

from ...modbus_slave.tests.dummies import Dummy_serial_intf_factory, Dummy_timer_factory
from ..serial import Recup_serial_intf
from ..device import Recup_device
from .. import funcs as func


class Base_test_func:
    def create_device(self) -> Recup_device:
        return Recup_device(Recup_serial_intf("COM5", Dummy_serial_intf_factory()))


class Test_recup_funcs(Base_test_func):
    def test_init_all(self):
        """Check if init pases without any address violation."""
        funcs: list[Device_func] = []
        device = self.create_device()
        try:
            funcs.append(func.Unknown_funcs(device))
            funcs.append(func.Exhaust_fan(device, func.Fan_linear_conv()))
            funcs.append(func.Supply_fan(device, func.Fan_linear_conv()))
            funcs.append(func.GWC(device))
            funcs.append(func.Error(device, Dummy_timer_factory()))
            funcs.append(func.Bypass(device))
            funcs.append(func.Heater(device))
            funcs.append(func.Pump(device))
            funcs.append(func.Thermometer_01(device))
            funcs.append(func.Thermometer_02(device))
            funcs.append(func.Thermometer_03(device))
            funcs.append(func.Thermometer_04(device))
            funcs.append(func.Thermometer_05(device))

            device.holding_registers.clean_up()
        except Exception as ec:
            pytest.fail(f"Exception while initializing functions: {ec}")


class Base_test_fan(Base_test_func):
    def set_helper(self, fan: func.Fan_base, min: int, max: int):
        try:
            for i in range(min, max + 1):
                fan.set(i)
        except Exception:
            pytest.fail(f"Value {i} should be within range of the fan.")

        for i in range(min - 5, min - 1):
            try:
                fan.set(i)
                pytest.fail(f"Value {i} should not be within range of the fan.")
            except Exception:
                assert True

        for i in range(max + 1, max + 6):
            try:
                fan.set(i)
                pytest.fail(f"Value {i} should not be within range of the fan.")
            except Exception:
                assert True


class Test_supply_fan(Base_test_fan):
    @pytest.fixture
    def fixt(self) -> func.Supply_fan:
        device = self.create_device()
        return func.Supply_fan(device, func.Fan_non_conv())

    def test_set(self, fixt: func.Fan_base):
        self.set_helper(fixt, 0, 99)


class Test_supply_fan_linear(Test_supply_fan):
    @pytest.fixture
    def fixt(self) -> func.Supply_fan:
        device = self.create_device()
        return func.Supply_fan(device, func.Fan_linear_conv())


class Test_exhaust_fan(Base_test_fan):
    @pytest.fixture
    def fixt(self) -> func.Exhaust_fan:
        device = self.create_device()
        self.supply = func.Supply_fan(device, func.Fan_non_conv())
        return func.Exhaust_fan(device, func.Fan_non_conv())

    def test_set(self, fixt: func.Exhaust_fan):
        for i in range(0, 100):
            self.supply.set(i)
            min_ = max(0, i - 20)
            max_ = min(99, i)
            assert fixt.get_min() == min_
            assert fixt.get_max() == max_
            self.set_helper(fixt, min_, max_)


class Test_error(Base_test_func):
    @pytest.fixture
    def fixt(self) -> func.Error:
        self.device = self.create_device()
        self.timers = Dummy_timer_factory()
        return func.Error(self.device, self.timers)

    def test_timeout(self, fixt: func.Error) -> None:
        """Check if timeout error appears after timer fires."""
        assert len(fixt.get()) == 0

        self.timers.get_last_timer().fire()
        assert fixt.get() == [func.Error.Error.E8]
        fixt.reset()
        assert fixt.get() == [func.Error.Error.E8]
        fixt._timer.callb()
        assert fixt.get() == []

    def test_clean(self, fixt: func.Error) -> None:
        """Check if user can delete errors."""
        assert len(fixt.get()) == 0

        self.device.holding_registers.set_single_val_ext(
            func.Error._addr_err, int("11111111", 2)
        )
        assert len(fixt.get()) == 4

        for i in range(func.Error._addr_01, func.Error._addr_05 + 1):
            self.device.holding_registers.set_single_val_ext(i, int("11111111", 2))
        errs = fixt.get()
        assert len(fixt.get()) == 9

        fixt.reset()
        assert len(fixt.get()) == 9

        self.device.holding_registers.set_single_val_ext(
            func.Error._addr_err, int("00000000", 2)
        )
        fixt.reset()
        assert len(fixt.get()) == 5

        for i in range(func.Error._addr_01, func.Error._addr_05 + 1):
            self.device.holding_registers.set_single_val_ext(i, int("00000000", 2))
        assert len(fixt.get()) == 0
