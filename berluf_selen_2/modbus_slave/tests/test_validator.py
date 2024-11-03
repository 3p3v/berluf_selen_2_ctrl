"""Memory fixt tests."""

import copy
from typing import override
import pytest

from ..validator import (
    Bigger_equal_handler,
    Equal_handler,
    Memory_validator,
    One_of_handler,
    Setter_any_validator,
    Setter_validator,
    Validator,
)


class Base_test_validator:
    """Generic fixt tests."""

    addrs: list[int] = [2, 3, 4, 6, 8, 10, 11, 12]

    def test_validate(self, fixt: Validator) -> None:
        """Address validation test."""
        try:
            fixt.validate(2, 3)
        except Exception as ec:
            pytest.fail(f"Correct range of addresses raised error: {ec}")

        try:
            fixt.validate(10, 1)
        except Exception as ec:
            pytest.fail(f"Address connrect but got invalidated: {ec}")

        try:
            fixt.validate(6, 3)
            pytest.fail("Address range should get invalidated.")
        except Exception:
            assert True


class Test_memory_validator(Base_test_validator):
    """Memory_validator tests."""

    @pytest.fixture
    def fixt(self) -> Validator:
        return Memory_validator(self.addrs)


class Test_setter_validator(Base_test_validator):
    """Value fixt tests."""

    @pytest.fixture
    def fixt(self) -> Setter_validator:
        return Setter_validator(self.addrs)

    def test_validate_vals(self, fixt: Setter_validator) -> None:
        """Test values validation."""
        fixt.update_handler(2, Bigger_equal_handler(10))
        fixt.update_handler(3, One_of_handler([1, 9, 12]))
        fixt.update_handler(10, Equal_handler(10))
        fixt.update_handler(11, Equal_handler(11))
        fixt.update_handler(12, Equal_handler(12))

        try:
            for v in range(10, 100):
                fixt.validate_val(2, v)
        except Exception:
            pytest.fail(f"Validation should not fail with value: {v}.")

        try:
            fixt.validate_val(2, 9)
            pytest.fail("Values should get invalidated.")
        except Exception:
            assert True

        try:
            for v in [1, 9, 12]:
                fixt.validate_val(3, v)
        except Exception:
            pytest.fail("Validation should not fail.")

        try:
            fixt.validate_val(3, 8)
            pytest.fail("Values should get invalidated.")
        except Exception:
            assert True

        try:
            fixt.validate_vals(10, [10, 11, 12])
        except Exception:
            pytest.fail("Validation should not fail.")

        try:
            fixt.validate_vals(10, [11, 12, 13])
            pytest.fail("Values should have got invalidated.")
        except Exception:
            assert True

    def test_validate_vals_out_of_range(self, fixt: Setter_validator) -> None:
        """Check if validation failes using out of range addresses."""
        try:
            for a, v in {13: 11, 14: 12, 15: 13}.items():
                fixt.validate_val(a, v)
                pytest.fail("Validation should have failed.")
        except Exception:
            assert True


class Test_setter_any_validator_tests(Base_test_validator):
    @pytest.fixture
    def fixt(self) -> Setter_any_validator:
        return Setter_any_validator()

    @override
    def test_validate(self, fixt: Validator) -> None:
        """Address validation test."""
        try:
            fixt.validate(2, 3)
        except Exception as ec:
            pytest.fail(f"Correct range of addresses raised error: {ec}")

        try:
            fixt.validate(10, 1)
        except Exception as ec:
            pytest.fail(f"Address correct but got invalidated: {ec}")

        try:
            fixt.validate(6, 3)
        except Exception:
            pytest.fail("Out of range address should not have been validated.")

    @override
    def test_validate_vals_out_of_range(self, fixt: Setter_validator) -> None:
        """Check if validation failes using out of range addresses."""
        try:
            for a, v in {13: 11, 14: 12, 15: 13}.items():
                fixt.validate_val(a, v)
        except Exception:
            pytest.fail("Validation shouldn't have failed.")
