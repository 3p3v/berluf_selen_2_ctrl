from .observer_func.callb import Callb_store, Invoke_callb_store
from .observer_func.func import Observer_func
from .validator import (
    Memory_validator,
    Setter_validator,
    Validator,
    Validator_handler,
)


class Memory:
    """Represents a Modbus memory fragment."""

    def __init__(
        self,
        setter_validator: Setter_validator,
        master_setter_validator: Setter_validator,
        callbs: Callb_store,
        invoke_callbs: Invoke_callb_store,
    ) -> None:
        # Validate self setter
        self._setter_validator = setter_validator
        # Validate master setter
        self._master_setter_validator = master_setter_validator
        # Callbacks to run when value changes
        self._callbs = callbs
        # Callbacks to run when received data from master
        self._invoke_callbs = invoke_callbs

    def _get_single_val(self, addr: int) -> int:
        raise NotImplementedError()

    def _get_multi_val(self, addr: int, count: int) -> list[int]:
        raise NotImplementedError()

    def get_single_val(self, addr: int) -> int:
        """Get single registry."""
        return self._get_single_val(addr)

    def _set_single_val(self, addr: int, val: int) -> None:
        raise NotImplementedError()

    def _set_multi_val(self, addr: int, val: list[int]) -> None:
        raise NotImplementedError()

    def _set_single_val_intf(
        self, addr: int, val: int, invoker: Observer_func | None
    ) -> None:
        self._setter_validator.validate_val(addr, val)
        if self._get_single_val(addr) != val:
            self._set_single_val(addr, val)
            self._callbs.run_callbs(addr, [val], invoker)

    def _set_multi_val_intf(
        self, addr: int, val: list[int], invoker: Observer_func | None
    ) -> None:
        self._setter_validator.validate_vals(addr, val)
        run_callbs = self._get_multi_val(addr, len(val))
        self._set_multi_val(addr, val)
        # Run callbacks if anything changed
        self._run_callbs_if_changed(addr, val, run_callbs)
                
    def _run_callbs_if_changed(self, address: int, vals: list[int], current: list[int]):
        run_callbs = [r != v for r, v in zip(current, vals)]
        if all(run_callbs):
            # All values changed
            self._callbs.run_callbs(address, vals)
        else:
            # Run only callbacks for addresses that changed
            faddr = address
            cvals = []
            for a, v, c in zip(range(address, address + len(vals)), vals, run_callbs):
                if (c):
                    cvals.append(v)
                elif len(cvals):
                    self._callbs.run_callbs(faddr, cvals)
                    faddr = a + 1
                    cvals.clear()
                else:
                    faddr = a + 1
                    
            if len(cvals):
                self._callbs.run_callbs(faddr, cvals)

    def get_callb_service(self) -> Callb_store:
        """Get callback service used for callbacks running when registry value changes."""
        return self._callbs

    def get_invoke_callb_service(self) -> Invoke_callb_store:
        """Get callback service used for callbacks running when registry value changes."""
        return self._invoke_callbs

    def get_address_list(self) -> list[int]:
        """List all addresses managed by this memory."""
        raise NotImplementedError()

    def get_all_single_vals(self) -> dict[int, int]:
        """Retreive values from memory."""
        raise NotImplementedError()

    def get_all_single_sorted_vals(self) -> list[tuple[int, int]]:
        """Retreive values from memory, sorted by key."""
        return sorted(self.get_all_single_vals().items())

    def get_all_multi_vals(self) -> dict[int, list[int]]:
        """Retreive values from memory in a more friendly form."""
        single_vals = self.get_all_single_sorted_vals()

        if len(single_vals) > 0:
            # Algh
            addr = single_vals[0][0]
            offset = 1
            val_list = [single_vals[0][1]]
            # Return var
            multi_vals = {addr: val_list}
            # Algh
            for a, v in single_vals[1:]:
                if a == addr + offset:
                    val_list.append(v)
                    offset += 1
                else:
                    val_list = [v]
                    multi_vals[a] = val_list
                    addr = a
                    offset = 1

            return multi_vals

        return {}


class Memory_rw(Memory):
    """Represents a Modbus readable/writeable memory (readable by masster)."""

    class Memory_setter:
        """Class returned when a function registes for setting variables."""

        def __init__(self, impl: Memory, validator: Validator) -> None:
            self._impl = impl
            # Validator checking if a function has a right to change the specyfied address
            self._validator = validator

        def set_single_val(
            self, addr: int, val: int, invoker: Observer_func | None = None
        ) -> None:
            """Change single registry."""
            self._validator.validate(addr)
            self._impl._set_single_val_intf(addr, val, invoker)
            return

        def set_multi_val(
            self, addr: int, val: list[int], invoker: Observer_func | None = None
        ) -> None:
            """Change many continous registries."""
            self._validator.validate(addr)
            self._impl._set_multi_val_intf(addr, val, invoker)
            return

        def update_handler(self, addr: int, handler: Validator_handler) -> None:
            """Update setting validation."""
            self._impl._setter_validator.update_handler(addr, handler)
            return

    def __init__(
        self,
        setter_validator: Setter_validator,
        master_setter_validator: Setter_validator,
        callbs: Callb_store,
        invoke_callbs: Invoke_callb_store,
    ):
        super().__init__(
            setter_validator,
            master_setter_validator,
            callbs,
            invoke_callbs,
        )
        # List for tracking addresses managed by functions
        self._given_addrs: list[int] | None = []
        return

    def get_setter(
        self, addr_valids: dict[int, list[Validator_handler]]
    ) -> Memory_setter:
        """Register a function for setting variables by getting a setter object."""
        if self._given_addrs is not None:
            # Check if all addrs exist
            all_addrs = []
            for addrs, valids in addr_valids.items():
                all_addrs.extend(range(addrs, addrs + len(valids)))

            if any(a in self._given_addrs for a in all_addrs):
                raise RuntimeError("Address has already been taken.")

            for a in all_addrs:
                self._setter_validator.validate(a)

            # Update validators
            offset = 0
            for valids in addr_valids.values():
                for a, v in zip(all_addrs[offset:], valids):
                    self._given_addrs.append(a)
                    self._setter_validator.update_handler(a, v)

                offset += len(valids)

            return Memory_rw.Memory_setter(self, Memory_validator(all_addrs))

        raise RuntimeError("Initialization has already been completed")

    def get_setter_unsafe(self, addrs: list[int]) -> Memory_setter:
        """Get setter without checking if address has already been taken."""
        for a in addrs:
            self._setter_validator.validate(a)

        return Memory_rw.Memory_setter(self, Memory_validator(addrs))

    def clean_up(self, check: bool = True) -> None:
        """Clean up after initializing all functions."""
        if self._given_addrs is not None:
            if len(self._given_addrs) == 0:
                raise Warning("None of the addresses has been distributed.")

            if (
                not all(
                    g in self.get_all_single_vals().keys() for g in self._given_addrs
                )
                and check
            ):
                raise Warning("Some of the addresses has not been distributed.")

            # Clean up
            self._given_addrs = None
