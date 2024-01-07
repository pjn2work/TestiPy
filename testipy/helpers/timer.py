from __future__ import annotations

from time import sleep
from datetime import datetime, timedelta


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
