from __future__ import annotations

from datetime import datetime
from typing import Union, List, Tuple, Dict, NamedTuple

from testipy.configs.enums_data import SEVERITY_STATES_ORDER


class LAP(NamedTuple):
    state: str
    qty: int
    total_seconds: float
    reason_of_state: str
    description: str
    exc_value: Union[BaseException, None]
    timed_all_end: datetime


class StateCounter:

    def __init__(self, states: List[str] = SEVERITY_STATES_ORDER):
        # state counters
        self._counter: Dict[str, int] = dict()
        for state in states:
            self._counter[state] = 0

        # reason of state counter for each state:
        # self._reasons_of_states["PASSED"]["OK"] = 5
        # self._reasons_of_states["PASSED"]["good"] = 1
        self._reasons_of_states: Dict[str, Dict[str, int]] = dict()
        for state in self._counter:
            self._reasons_of_states[state] = dict()

        # Consecutive counter
        self._last_state = ""
        self._last_reason_of_state = ""
        self._last_consecutive_qty = 0

        # Timming vars
        self._timed_laps: List[LAP] = []
        self._timed_all_begin = self._timed_all_end = datetime.now()

    def get_begin_time(self) -> datetime:
        return self._timed_all_begin

    def get_end_time(self) -> datetime:
        return self._timed_all_end

    def get_timed_total_elapsed(self) -> float:
        """
        :return: float of elapsed_time_in_seconds since the __init__ of class until last state change
        :rtype: float
        """
        return (self._timed_all_end - self._timed_all_begin).total_seconds()

    # sets the end-time to now but also makes the next state starting from now
    def set_state_starting_from_now(self) -> StateCounter:
        self._timed_all_end = datetime.now()
        return self

    def __add_time_lap(self, state: str, qty: int = 1, reason_of_state: str = "", description: str = "", exc_value: BaseException = None):
        timed_current_state_begin, self._timed_all_end = self._timed_all_end, datetime.now()
        total_seconds = (self._timed_all_end - timed_current_state_begin).total_seconds()

        # append time lap
        self._timed_laps.append(LAP(state, qty, total_seconds, reason_of_state, description, exc_value, self._timed_all_end))

    def get_timed_last_lap(self) -> Union[LAP, None]:
        """
        :return: tuple with LAP(state_name, qty, elapsed_time_in_seconds, reason_of_state, description, exception, timestamp), or None
        :rtype: tuple
        """
        if len(self._timed_laps) > 0:
            return self._timed_laps[-1]
        return None

    def get_timed_laps(self, state: str = None) -> List[LAP]:
        """
        :return: list with tuples (state_name, qty, elapsed_time_in_seconds, reason_of_state, description, exception, timestamp)
        :rtype: list
        """
        if state:
            return [lap for lap in self._timed_laps if lap.state == state]
        return self._timed_laps

    def get_sum_time_laps(self) -> float:
        """
        :return: float of sum of all time laps
        :rtype: float
        """
        return sum([lap.total_seconds for lap in self._timed_laps])

    def __inc_consecutive(self, state: str, qty: int = 1):
        if state == self._last_state:
            self._last_consecutive_qty += qty
        else:
            self._last_consecutive_qty = qty
            self._last_state = state

    def get_last_state(self) -> str:
        """
        :return: last state_name increased
        :rtype: str
        """
        return self._last_state

    def get_last_reason_of_state(self, state: str = None) -> str:
        """
        :return: str with last reason
        :rtype: str
        """
        if state:
            if filter_by_state := self.get_timed_laps(state):
                return str(filter_by_state[-1].reason_of_state)
            else:
                return ""
        return self._last_reason_of_state

    def get_first_reason_of_state(self, state: str = None) -> str:
        """
        :return: str with first reason
        :rtype: str
        """
        if state:
            if filter_by_state := self.get_timed_laps(state):
                return filter_by_state[0].reason_of_state
            else:
                return ""
        elif len(self._timed_laps) > 0:
            return self._timed_laps[0].reason_of_state
        return ""

    def get_last_consecutive_qty(self, state: str = None) -> int:
        """
        :param state: str [default=None] with state_name, if None then last_state
        :return: int with total consecutive increases
        :rtype: int
        """
        if state is None or state == self._last_state:
            return self._last_consecutive_qty
        return 0

    def get_reasons_of_states(self) -> Dict[str, Dict[str, int]]:
        """
        :return: dict of status with dict of reasons (for each status)
        :rtype: dict
        """
        return self._reasons_of_states

    def get_reasons_of_state(self, state: str) -> Dict[str, int]:
        """
        :param state: str with state_name
        :return: dict with total incremented RoS, or None
        :rtype: dict
        """
        return self._reasons_of_states.get(state, dict())

    def get_major_reason_of_state(self, state: str) -> str:
        """
        :param state: str with state_name
        :return: string with major reason of state, or None
        :rtype: str
        """
        ros_dict = self.get_reasons_of_state(state)
        if len(ros_dict) > 0:
            max_occurrences = max([qty for ros, qty in ros_dict.items()])
            for ros, qty in ros_dict.items():
                if qty == max_occurrences and ros:
                    return str(ros)
        return ""

    def get_state_by_severity(self) -> Tuple[str, str]:
        for state in SEVERITY_STATES_ORDER:
            if self._counter[state] > 0:
                return state, self.get_last_reason_of_state(state) or self.get_major_reason_of_state(state)
        return "", ""

    def __inc_reason_of_state(self, state: str, qty: int, reason_of_state: str):
        if state not in self._reasons_of_states:
            self._reasons_of_states[state] = dict()

        self._last_reason_of_state = reason_of_state
        if reason_of_state:
            if reason_of_state in self._reasons_of_states[state]:
                self._reasons_of_states[state][reason_of_state] += qty
            else:
                self._reasons_of_states[state][reason_of_state] = qty

    def inc_state(self, state: str, reason_of_state: str = "", description: str = "", qty: int = 1, exc_value: BaseException = None) -> StateCounter:
        """
        :param state: str with state_name
        :param reason_of_state: str explaining the reason for state
        :param description: str explaining the executed step for this state
        :param qty: int [default=1] with quantity to increase
        :return: self
        :rtype: StateCounter
        """
        if reason_of_state and not isinstance(reason_of_state, str):
            reason_of_state = str(reason_of_state)

        if state and qty > 0:
            self._counter[state] = self._counter.get(state, 0) + qty
            self.__inc_reason_of_state(state, qty, reason_of_state)
            self.__inc_consecutive(state, qty)
            self.__add_time_lap(state, qty, reason_of_state, description, exc_value)
        return self

    def inc_states(self, other: StateCounter) -> StateCounter:
        """
        :param other: same as self
        :return: self
        :rtype: StateCounter
        """
        if isinstance(other, StateCounter):
            for state in other:
                if state in self._counter:
                    self._counter[state] += other[state]
                else:
                    self._counter[state] = other[state]

                for ros, qty in other.get_reasons_of_state(state).items():
                    self.__inc_reason_of_state(state, qty, ros)

            # append to current, the other counters
            for other_lap_data in other.get_timed_laps():
                self._timed_laps.append(other_lap_data)

            # sort current counters by timestamp
            self._timed_laps = sorted(self._timed_laps, key=lambda lap: lap.timed_all_end, reverse=False)

            if other._timed_all_begin < self._timed_all_begin:
                self._timed_all_begin = other._timed_all_begin

            if other._timed_all_end > self._timed_all_end:
                self._timed_all_end = other._timed_all_end

        return self

    def all(self, state: str) -> bool:
        """
        :param state: str with state_name
        :return: True if this state is equal to total, and other states == 0
        :rtype: bool
        """
        return (state in self._counter) and (self.get_total() > 0) and (self._counter[state] == self.get_total())

    def any(self, state: str) -> bool:
        """
        :param state: str with state_name
        :return: True if that state has at least 1 RoS
        :rtype: bool
        """
        return self._counter.get(state, 0) > 0

    def reset(self) -> StateCounter:
        for state in self._counter:
            self._counter[state] = 0
            self._reasons_of_states[state].clear()

        self._last_state = ""
        self._last_consecutive_qty = 0

        self._timed_laps.clear()
        self._timed_all_begin = self._timed_all_end = datetime.now()

        return self

    def get_summary_per_state(self) -> List[Tuple[str, int, float, Dict[str, int]]]:
        return [(state, value, self.get_state_percentage(state), self.get_reasons_of_state(state)) for state, value in self._counter.items()]

    def get_summary_per_state_without_ros(self) -> List[Tuple[str, int, float]]:
        return [(state, value, self.get_state_percentage(state)) for state, value in self._counter.items()]

    def get_dict(self) -> Dict[str, int]:
        """
        :return: dict with state counters
        :rtype: dict
        """
        return self._counter

    def get_total(self) -> int:
        """
        :return: sum(all state counters)
        :rtype: int
        """
        return sum(self._counter.values())

    def get_state_percentage(self, state: str) -> float:
        """
        :param state: str with state_name
        :return: float with percentage of that state
        :rtype: float
        """
        total = self.get_total()
        counter = self._counter.get(state, 0)
        if counter > 0 and total > 0:
            return counter * 100 / total
        return 0.0

    def get_totals_percentage(self, prefix_ident: str = "") -> list[str]:
        """
        :param prefix_ident: str with prefix
        :return: list of str(prefix state_name=state%)
        :rtype: list
        """
        return [f"{prefix_ident}{state}={self.get_state_percentage(state):.2f}%" for state in self._counter]

    def summary(self, verbose: bool = True) -> str:
        """
        :return: multiline string with totals, status [qty] RoS
        :rtype: str
        """
        res = f"{str(self)}"
        if verbose:
            max_state_len = max([len(s) for s in self._reasons_of_states])
            for state in self._reasons_of_states:
                for i, (ros, qty) in enumerate(self.get_reasons_of_state(state).items()):
                    res += f"\n{state:{max_state_len}} [{qty:4}] {ros}" if i == 0 else f"\n{' '*max_state_len} [{qty:4}] {ros}"
        return res

    def get_ros_totals(self) -> Dict[str, int]:
        """
        :return: dict with 'reason_of_state': total_cases, regardless of the state
        :rtype dict
        """
        result = dict()
        for state_ros in self._reasons_of_states.values():
            for ros, qty in state_ros.items():
                if ros not in result:
                    result[ros] = qty
                else:
                    result[ros] += qty
        return result

    def items(self):
        return self._counter.items()

    def export_summary_to_file(self, filename: str):
        with open(filename, "w+") as f:
            f.write("\n".join([f"{state}: {qty}" for state, qty in self._counter.items()]))

    def __str__(self):
        state_total = [f"{state}={total}" for state, total in self._counter.items()]
        state_total.append(f"Total={self.get_total()}")
        return ", ".join(state_total)

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, list(self._counter.keys()))

    def __len__(self):
        return len(self._counter)

    def __contains__(self, key):
        return key in self._counter

    def __getitem__(self, key):
        if key in self._counter:
            return self._counter[key]
        return None

    def __setitem__(self, key, value):
        self._counter[key] = value
        if key not in self._reasons_of_states:
            self._reasons_of_states[key] = dict()

    def __delitem__(self, key):
        del self._counter[key]
        del self._reasons_of_states[key]

    def __iter__(self):
        for key in self._counter:
            yield key
