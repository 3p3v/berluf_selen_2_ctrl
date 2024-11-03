"""Base classes for functions observing addresses' values."""


class Device_func:
    """Base class for some functionality of a device."""


class Invokable_func(Device_func):
    """Class observing if something was invoked."""

    def callb(self) -> None:
        """Run a callback when some state changes."""
        raise NotImplementedError()


class Observer_func(Device_func):
    """Class observing changes in addresses."""

    def callb(self, addr: int, vals: list[int]) -> None:
        """Run a callback when the value of an observed address changes."""
        raise NotImplementedError()
