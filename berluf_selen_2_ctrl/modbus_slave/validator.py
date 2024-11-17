from typing import override


class Validator:
    def validate(self, addr: int, count: int = 1) -> None:
        raise NotImplementedError()


class Validator_handler:
    def validate(self, val: int) -> bool:
        raise NotImplementedError()


class Equal_handler(Validator_handler):
    """Return true if values are equal."""

    def __init__(self, val_eq: int) -> None:
        self._val_eq = val_eq

    @override
    def validate(self, val: int) -> bool:
        return val == self._val_eq


class One_of_handler(Validator_handler):
    """Return true if values are equal."""

    def __init__(self, val_eq: list[int]) -> None:
        self._val_eq = val_eq

    @override
    def validate(self, val: int) -> bool:
        return val in self._val_eq


class Smaller_handler(Validator_handler):
    """Return true if given value is smaller."""

    def __init__(self, val_big: int) -> None:
        self._val_big = val_big

    @override
    def validate(self, val: int) -> bool:
        return val < self._val_big


class Bigger_equal_handler(Smaller_handler):
    def __init__(self, val_small: int) -> None:
        super().__init__(val_small)

    @override
    def validate(self, val: int) -> bool:
        return not super().validate(val)


class Bigger_handler(Validator_handler):
    """Return true if given value is smaller."""

    def __init__(self, val_small: int) -> None:
        self._val_small = val_small

    @override
    def validate(self, val: int) -> bool:
        return val > self._val_small


class Smaller_equal_handler(Bigger_handler):
    def __init__(self, val_big: int) -> None:
        super().__init__(val_big)

    @override
    def validate(self, val: int) -> bool:
        return not super().validate(val)


class Many_handler(Validator_handler):
    def __init__(self, valids: list[Validator_handler]) -> None:
        self._valids = valids
        return

    @override
    def validate(self, val: int) -> bool:
        return all(x.validate(val) for x in self._valids)


class None_validator(Validator_handler):
    @override
    def validate(self, val: int) -> bool:
        return False


class Memory_validator(Validator):
    def __init__(self, addrs: list) -> None:
        self._addrs = addrs
        return

    @override
    def validate(self, addr: int, count: int = 1) -> None:
        for a in range(addr, addr + count):
            if a in self._addrs:
                continue

            raise RuntimeError(f"Address {a} is inaccessable in this context.")


class Setter_validator(Validator):
    # def __init__(self, addr_valids: dict[int, list[Validator_handler]]) -> None:
    def __init__(self, addr: list[int]) -> None:
        self._addrs: dict[int, Validator_handler] = {}
        # Add vallidators one by one
        for a in addr:
            # One validator for each adddress
            self._addrs[a] = None_validator()

    @override
    def validate(self, addr: int, count: int = 1) -> None:
        for a in range(addr, addr + count):
            if a in self._addrs:
                continue

            raise RuntimeError(f"Address {a} is inaccessable in this context.")

    def validate_val(self, addr: int, val: int) -> None:
        """Check if value is valid."""
        self.validate_vals(addr, [val])

    def validate_vals(self, addr: int, val: list[int]) -> None:
        """Check if values are valid."""
        for a, v in zip(range(addr, addr + len(val)), val):
            ar = self._addrs.get(a)
            if ar is not None:
                if not ar.validate(v):
                    raise RuntimeError(
                        f"Value of the address {addr} can not be equal {v}."
                    )

                continue

            raise RuntimeError(f"Address {addr} is inaccessable in this context.")

    def update_handler(self, addr: int, handler: Validator_handler) -> None:
        """Update the validation handler."""
        if self._addrs.get(addr) is not None:
            self._addrs[addr] = handler
        else:
            raise RuntimeError(f"Element {addr} is not under validation in this unit.")


class Setter_any_validator(Setter_validator):
    """Setter validator not checking validity of any address that was not specyfied."""

    def __init__(self) -> None:
        super().__init__([])

    @override
    def validate(self, addr: int, count: int) -> None:
        """Valiate any address."""
        return

    @override
    def validate_vals(self, addr: int, val: list[int]) -> None:
        for a, v in zip(range(addr, addr + len(val)), val):
            ar = self._addrs.get(a)
            if ar is not None:
                # Addresse's values specyfied, validate
                if not ar.validate(v):
                    raise RuntimeError(
                        f"Value of the address {addr} can not be equal {v}."
                    )

                return

    @override
    def update_handler(self, addr: int, handler: Validator_handler) -> None:
        self._addrs[addr] = handler
