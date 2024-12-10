from __future__ import annotations

import typing
import math
from datetime import datetime, timedelta
from time import sleep


class Timer:

    def __init__(self, seconds: float = 0.0, **kwargs):
        self.timer_end = datetime.now()
        self.set_timer_for(seconds=seconds, **kwargs)

    def set_timer_for(self, seconds: float = 0.0, **kwargs) -> Timer:
        self.timer_end = datetime.now() + timedelta(seconds=seconds, **kwargs)
        return self

    def is_timer_over(self) -> bool:
        return datetime.now() >= self.timer_end

    def is_timer_valid(self) -> bool:
        return datetime.now() < self.timer_end

    def seconds_left(self) -> float:
        sl = (self.timer_end - datetime.now()).total_seconds()
        return max(0, sl)

    def sleep_until_over(self) -> Timer:
        sleep(self.seconds_left())
        return self

    @staticmethod
    def sleep_for(seconds: float):
        if seconds > 0.0:
            sleep(seconds)

    def sleep_for_if_not_over(self, seconds: float, **kwargs) -> Timer:
        if datetime.now() + timedelta(seconds=seconds, **kwargs) > self.timer_end:
            self.sleep_until_over()
        else:
            self.sleep_for(seconds)
        return self


class Sleep:
    """
    A class that sleeps between atempts, with a timeout and wait intervals.

    Attributes:
       timeout_sec (float): The total timeout in seconds.
       wait_min_sec (float): The minimum wait time in seconds between attempts.
       wait_max_sec (float): The maximum wait time in seconds between attempts.

    Usage:
        pulling = Sleep(timeout_sec=2, wait_min_sec=0.1, wait_max_sec=0.5)
        current_time = datetime.now()
        for attempt in pulling.camel():
            print(f'Attempt {attempt}', datetime.now() - current_time)
            current_time = datetime.now()
    """

    def __init__(self, timeout_sec: float, wait_min_sec: float, wait_max_sec: float, max_attempts: int = 0):
        """
        Initializes the class with the given timeout and wait intervals.

        Args:
           timeout_sec (int): The total timeout in seconds.
           wait_min_sec (int): The minimum wait time in seconds between attempts.
           wait_max_sec (int): The maximum wait time in seconds between attempts.
        """
        self.timeout_sec = timeout_sec
        self.wait_min_sec = min(wait_min_sec, wait_max_sec)
        self.wait_max_sec = max(wait_min_sec, wait_max_sec)
        self.max_attempts = max_attempts
        self.reset()

    def reset(self):
        self._timer_end = datetime.now() + timedelta(seconds=self.timeout_sec)

    def flat(self) -> typing.Generator[int, None, None]:
        """
        A generator that yields the number of attempts made until the timeout is reached, with flat sleep.

        Yields:
           int: The current attempt number.
        """
        time_left = (self._timer_end - datetime.now()).total_seconds()
        attempt = 0

        while time_left > 0.0 and (self.max_attempts <= 0 or attempt < self.max_attempts):
            sleep(min(self.wait_min_sec, time_left))
            attempt += 1
            yield attempt

            time_left = (self._timer_end - datetime.now()).total_seconds()

    def ramp_down(self) -> typing.Generator[int, None, None]:
        """
        A generator that yields the number of attempts made until the timeout is reached, ramp down from max until min.

        Yields:
        int: The current attempt number.
        """
        time_left = (self._timer_end - datetime.now()).total_seconds()
        current_wait_time = self.wait_max_sec
        attempt = 0

        while time_left > 0.0 and current_wait_time > 0.0 and (self.max_attempts <= 0 or attempt < self.max_attempts):
            sleep(min(current_wait_time, time_left))
            attempt += 1
            yield attempt

            time_left = (self._timer_end - datetime.now()).total_seconds()
            amplitude = (time_left / self.timeout_sec) * (self.wait_max_sec - self.wait_min_sec)
            current_wait_time = self.wait_min_sec + amplitude

    def ramp_up(self) -> typing.Generator[int, None, None]:
        """
        A generator that yields the number of attempts made until the timeout is reached, ramp up from min until max.

        Yields:
        int: The current attempt number.
        """
        time_left = (self._timer_end - datetime.now()).total_seconds()
        current_wait_time = self.wait_min_sec
        attempt = 0

        while time_left > 0.0 and current_wait_time > 0.0 and (self.max_attempts <= 0 or attempt < self.max_attempts):
            sleep(min(current_wait_time, time_left))
            attempt += 1
            yield attempt

            time_left = (self._timer_end - datetime.now()).total_seconds()
            amplitude = (1 - (time_left / self.timeout_sec)) * (self.wait_max_sec - self.wait_min_sec)
            current_wait_time = self.wait_min_sec + amplitude

    def camel(self) -> typing.Generator[int, None, None]:
        """
        A generator that yields the number of attempts made until the timeout is reached, in a camel sin(x) shape.

        Yields:
        int: The current attempt number.
        """
        time_left = (self._timer_end - datetime.now()).total_seconds()
        current_wait_time = self.wait_min_sec
        attempt = 0

        while time_left > 0.0 and current_wait_time > 0.0 and (self.max_attempts <= 0 or attempt < self.max_attempts):
            sleep(min(current_wait_time, time_left))
            attempt += 1
            yield attempt

            time_left = (self._timer_end - datetime.now()).total_seconds()
            amplitude = math.sin((time_left / self.timeout_sec) * math.pi)
            current_wait_time = amplitude * (self.wait_max_sec - self.wait_min_sec) + self.wait_min_sec
