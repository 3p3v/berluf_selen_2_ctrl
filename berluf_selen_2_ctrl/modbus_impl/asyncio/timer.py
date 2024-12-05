from ...modbus_slave.timer import Timer, Timer_factory
import asyncio
import math
from typing import Callable


class Asyncio_timer(Timer):
    def __init__(self, timeout: int, callb: Callable[[], None]):
        self._timeout = timeout
        self._callb = callb
        self._task: asyncio.Task | None = None
        # If cancellation procedure was called
        self._cancel_in_progress = False
        # Should be running
        self._is_on = False

    async def _job(self) -> None: 
        if not self._cancel_in_progress and self._is_on:
            await asyncio.sleep(self._timeout)
        else:
            self._task = None
            await self._stop_job()
            return

        self._task = None
        if not self._cancel_in_progress and self._is_on:
            self._is_on = False
            self._callb()
        else:
            await self._stop_job()

    async def _stop_job(self) -> None:
        # Do not cancel if called from _job procedure
        if self._task is not None:
            self._task.cancel()
            # Wait untill cancelled
            while not self._task.cancelled():
                await asyncio.sleep(0)

            self._task = None

        self._cancel_in_progress = False

        # Start timer again if user requested in the meanwhile (pending start if _if_on but the task was not started)
        if self._is_on is True:
            self._task = self._run_job()

    def start(self) -> None:
        if self._is_on is False:
            # Mark as turned on so can be cancelled
            self._is_on = True
            # Check if cancellation already in progress (task will be started in the stop procedure)
            if self._cancel_in_progress is False:
                self._task = self._run_job()
        else:
            raise RuntimeError("Timer already started.")

    def cancel(self) -> None:
        if self._is_on is True:
            # Mark as turned off
            self._is_on = False
            # Check if really started
            if self._cancel_in_progress is False:
                # Mark as cancel in progress
                self._cancel_in_progress = True
                # Unmark start
                self._run_stop_job()
        else:
            raise RuntimeError("Timer hasn't started yet.")

    def _run_stop_job(self) -> asyncio.Task:
        return asyncio.ensure_future(self._stop_job())

    def _run_job(self) -> asyncio.Task:
        return asyncio.ensure_future(self._job())


class Asyncio_timer_factory(Timer_factory):
    def create_timer(self, timeout: int, callb: Callable[[], None]) -> Timer:
        return Asyncio_timer(timeout, callb)

class Asyncio_interval_timer(Timer):
    def __init__(self, timeout: int, callb: Callable[[], None], interval: int):
        if interval > timeout:
            raise IndentationError("Interval cannot be longer than timeout")
        
        cycles = timeout / interval
        self._cycles = math.ceil(cycles)
        if self._cycles != cycles:
            raise Warning("Result of timeout and interval division is not an integer.")
        
        self._timeout = timeout
        self._interval = interval
        self._current_cycle = 0
        self._last_interval = self._timeout % self._interval
        if self._last_interval == 0:
            self._last_interval = self._interval
        
        self._callb = callb
        self._task: asyncio.Task | None = None
        # Should be running
        self._is_on = False
        
    def _stop(self):
        self._is_on = False
        self._current_cycle = 0

    async def _job(self) -> None:  # Implement separate stop job
        while self._current_cycle < self._cycles and self._is_on:
            self._current_cycle += 1
            if self._current_cycle == self._cycles:
                # Last cycle, shorter interval
                await asyncio.sleep(self._last_interval)
                if self._current_cycle == self._cycles and self._is_on:
                    self._stop()
                    self._callb()
            else:
                # Normal interval
                await asyncio.sleep(self._interval)
            
        self._stop()
        self._task = None

    def start(self) -> None:
        if self._is_on is False:
            # Mark as turned on so can be cancelled
            self._is_on = True
            # Check if cancellation already in progress (task will be started in the stop procedure)
            if self._task is None:
                self._task = self._run_job()
        else:
            raise RuntimeError("Timer already started.")

    def cancel(self) -> None:
        if self._is_on is True:
            # Mark as turned off
            self._is_on = False
            # Reset cycles 
            self._current_cycle = 0
        else:
            raise RuntimeError("Timer hasn't started yet.")

    def _run_job(self) -> asyncio.Task:
        return asyncio.ensure_future(self._job())


class Asyncio_interval_timer_factory(Timer_factory):
    def __init__(self, interval: int) -> None:
        super().__init__()
        self._interval = interval
    
    def create_timer(self, timeout: int, callb: Callable[[], None]) -> Timer:
        return Asyncio_interval_timer(timeout, callb, self._interval)
