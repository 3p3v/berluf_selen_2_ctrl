"""Memory validator tests."""

import copy
import pytest

from ..memory import (
    Memory,
)

from ..observer_func.callb import Callb_store, Invoke_callb_store

from ..validator import (
    Equal_handler,
    One_of_handler,
    Memory_validator,
    Setter_validator,
)

from .dummies import Dummy_memory_rw, Dummy_observer_func


class Test_memory_rw:
    """Memory_rw tests."""

    @pytest.fixture
    def fixt(self) -> Dummy_memory_rw:
        def get_addrs(m: dict[int, list[int]]) -> list[int]:
            mem = []
            for a, v in m.items():
                mem.extend(list(range(a, a + len(v))))

            return mem

        mem = {1: list(range(1, 5))}
        mem_master = {1: list(range(5, 10))}
        get_addr = get_addrs(mem)
        set_addr = get_addr
        get_addr_master = get_addrs(mem_master)
        set_addr_master = get_addr_master

        mem.update(mem_master)
        return Dummy_memory_rw(
            mem,
            # Validation from functions' side
            Setter_validator(set_addr),
            # Validation from masters' side
            Setter_validator(set_addr_master),
            # Callbacks corresponding to particular addresses
            Callb_store(),
            # Invoking observers after any action from master
            Invoke_callb_store(),
        )

    def test_setter_address_violation(self, fixt: Dummy_memory_rw) -> None:
        """Try to get setter to unsettable addresses."""
        # Try exceeeding settable range
        try:
            fixt.get_setter({1: [Equal_handler(x) for x in range(1, 10)]})
            pytest.fail("Addresses should not be settable.")
        except Exception:
            assert True

        try:
            fixt.get_setter_unsafe(list(range(1, 10)))
            pytest.fail("Addresses should not be settable.")
        except Exception:
            assert True

        # Check if not taken
        try:
            fixt.get_setter({1: [Equal_handler(x) for x in range(1, 5)]})
        except Exception:
            pytest.fail("Addresses should not be taken.")

    def test_setter_multi_violation(self, fixt: Dummy_memory_rw) -> None:
        """Try getting setter to the same address many times."""
        addrs = range(1, 5)

        s1 = fixt.get_setter({1: [Equal_handler(x) for x in addrs]})

        # Check if taken
        try:
            fixt.get_setter({1: [Equal_handler(x) for x in addrs]})
            pytest.fail("Setter should be taken.")
        except Exception:
            assert True

        # Try to take even though it's taken
        try:
            fixt.get_setter_unsafe({1: [Equal_handler(x) for x in addrs]})
        except Exception:
            pytest.fail(
                "Setter should have been taken by avoiding the safety mechanism."
            )

    def test_setting_and_callb(self, fixt: Dummy_memory_rw) -> None:
        """Check if values are set and callbacks are called."""
        addrs = range(1, 5)
        func = Dummy_observer_func(list(addrs), fixt.get_callb_service())
        s1 = fixt.get_setter({1: [One_of_handler([1, 2])]})

        # Should not call callback
        s1.set_single_val(1, 1, func)
        assert func.results.get(1) is None

        # Should not call callback
        s1.set_single_val(1, 1)
        assert func.results[1] == None

        # Should call callback
        s1.set_single_val(1, 2)
        assert func.results[1] == 2
