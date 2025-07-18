from libcpp cimport bool
from libcpp.vector cimport vector
from .flight_optim_ccexport cimport (
    flight_t, vertex_t, flight_time_t, flight_duration_t, cost_t,
    compute_day_scores as compute_day_scores_cc,
    Flight as FlightCC, FlightIndex as FlightIndexCC,
    DiffCostSettings as DiffCostSettingsCC,
    DayScorer as DayScorerCC,
    TravelCoverSettings as TravelCoverSettingsCC,
    TravelExtendSettings as TravelExtendSettingsCC,
    TravelSearchSettings as TravelSearchSettingsCC
)


cdef class FlightsList:
    cdef vector[FlightCC] flights

    cdef set_flights(self, const vector[FlightCC] &flights):
        self.flights = flights


cdef class FlighIndex:
    cdef FlightIndexCC flight_index

    cdef push_flight(
        self, id: flight_t, src: vertex_t, dst: vertex_t,
        start_time: flight_time_t, day_start_time: flight_time_t,
        duration: flight_duration_t
    ):
        self.flight_index.push_flight(id, src, dst, start_time, day_start_time, duration)

    cdef sort_flights(self):
        self.flight_index.sort_flights()

    cdef FlightsList select_flights(
        self, src: Set[vertex_t], dst: Set[vertex_t],
        start_time: flight_time_t, end_time: flight_time_t
    ):
        cdef vector[vertex_t] src_v = src
        cdef vector[vertex_t] dst_v = dst
        cdef vector[FlightCC] flights = self.flight_index.select_flights(
            src_v.data(), src_v.size(), dst_v.data(), dst_v.size(),
            start_time, end_time
        )
        r = FlightsList()
        r.set_flights(flights)
        return r


cdef class DiffCostSettings:
    cdef DiffCostSettingsCC cc_obj
    cdef bool _const

    def __init__(
        self,
        desired_value: cost_t = 0.0, down_factor: cost_t = 0.0, up_factor: cost_t = 0.0,
        const_: bool = False
    ):
        self.cc_obj.desired_value = desired_value
        self.cc_obj.down_factor = down_factor
        self.cc_obj.up_factor = up_factor
        self._const = const_

    @property
    def const(self) -> bool:
        return self._const

    @const.setter
    def const(self, value: bool):
        if self._const and not value:
            raise ValueError("Cannot make a const object mutable!")
        self._const = value

    @property
    def desired_value(self) -> cost_t:
        return self.cc_obj.desired_value

    @desired_value.setter
    def desired_value(self, value: cost_t):
        if self._const:
            raise AttributeError("Cannot modify a const DiffCostSettings object")
        self.cc_obj.desired_value = value

    @property
    def down_factor(self) -> cost_t:
        return self.cc_obj.down_factor

    @down_factor.setter
    def down_factor(self, value: cost_t):
        if self._const:
            raise AttributeError("Cannot modify a const DiffCostSettings object")
        self.cc_obj.down_factor = value

    @property
    def up_factor(self) -> cost_t:
        return self.cc_obj.up_factor

    @up_factor.setter
    def up_factor(self, value: cost_t):
        if self._const:
            raise AttributeError("Cannot modify a const DiffCostSettings object")
        self.cc_obj.up_factor = value

    def __repr__(self):
        return (
            f"DiffCostSettingsPy(desired_value={self.desired_value}, "
            f"down_factor={self.down_factor}, up_factor={self.up_factor})"
        )


cdef class DayScorer:
    cdef DayScorerCC cc_obj

    def __init__(
        self, day_costs: Tuple[cost_t, ...] = (),
        start_time: flight_time_t = 0, day_factor: flight_duration_t = 1
    ):
        cdef vector[cost_t] day_costs_v = day_costs
        self.cc_obj = compute_day_scores_cc(day_costs_v.data(), day_costs_v.size(), start_time, day_factor)

    def __repr__(self):
        return (
            f"DayScorer(\n"
            # TODO: day costs list
            f"  start_time={self.cc_obj.start_time!r},\n"
            f"  day_factor={self.cc_obj.day_factor!r}\n)"
        )


cdef class TravelCoverSettings:
    cdef TravelCoverSettingsCC cc_obj
    cdef bool _const

    def __init__(
        self,
        back_cost_factor: cost_t = 0.0, forward_cost_factor: cost_t = 0.0, time_back: flight_duration_t = 0,
        const_: bool = False
    ):
        self.cc_obj.back_cost_factor = back_cost_factor
        self.cc_obj.forward_cost_factor = forward_cost_factor
        self.cc_obj.time_back = time_back
        self._const = const_

    @property
    def const(self) -> bool:
        return self._const

    @const.setter
    def const(self, value: bool):
        if self._const and not value:
            raise ValueError("Cannot make a const object mutable!")
        self._const = value

    @property
    def back_cost_factor(self) -> cost_t:
        return self.cc_obj.back_cost_factor

    @back_cost_factor.setter
    def back_cost_factor(self, value: cost_t):
        if self._const:
            raise AttributeError("Cannot modify a const TravelCoverSettings object")
        self.cc_obj.back_cost_factor = value

    @property
    def forward_cost_factor(self) -> cost_t:
        return self.cc_obj.forward_cost_factor

    @forward_cost_factor.setter
    def forward_cost_factor(self, value: cost_t):
        if self._const:
            raise AttributeError("Cannot modify a const TravelCoverSettings object")
        self.cc_obj.forward_cost_factor = value

    @property
    def time_back(self) -> flight_duration_t:
        return self.cc_obj.time_back

    @time_back.setter
    def time_back(self, value: flight_duration_t):
        if self._const:
            raise AttributeError("Cannot modify a const TravelCoverSettings object")
        self.cc_obj.time_back = value

    def __repr__(self):
        return (
            f"TravelCoverSettings(back_cost_factor={self.back_cost_factor}, "
            f"forward_cost_factor={self.forward_cost_factor}, time_back={self.time_back})"
        )


cdef class TravelExtendSettings:
    cdef TravelExtendSettingsCC cc_obj

    def __init__(
        self, *,
        day_scorer: DayScorer,
        search_interval: flight_duration_t,
        flight_start_day_time: DiffCostSettings,
        first_flight_wait_time: DiffCostSettings,
        flight_wait_time: DiffCostSettings,
        flight_duration: DiffCostSettings,
        cover_settings: TravelCoverSettings,
        move_cost: cost_t,
        const_: bool = False
    ):
        self.cc_obj.day_scorer = day_scorer.cc_obj
        self.cc_obj.search_interval = search_interval
        self.cc_obj.flight_start_day_time = flight_start_day_time.cc_obj
        self.cc_obj.first_flight_wait_time = first_flight_wait_time.cc_obj
        self.cc_obj.flight_wait_time = flight_wait_time.cc_obj
        self.cc_obj.flight_duration = flight_duration.cc_obj
        self.cc_obj.cover_settings = cover_settings
        self.cc_obj.move_cost = move_cost
        self._const = const_

    @property
    def const(self) -> bool:
        return self._const

    @const.setter
    def const(self, value: bool):
        if self._const and not value:
            raise ValueError("Cannot make a const object mutable!")
        self._const = value

    @property
    def day_scorer(self) -> DayScorer:
        r = DayScorer()
        r.cc_obj = self.cc_obj.day_scorer
        return r

    @day_scorer.setter
    def day_scorer(self, value: DayScorer):
        if self._const:
            raise AttributeError("Cannot modify a const TravelExtendSettings object")
        self.cc_obj.day_scorer = value.cc_obj

    @property
    def search_interval(self) -> flight_duration_t:
        return self.cc_obj.search_interval

    @search_interval.setter
    def search_interval(self, value: flight_duration_t):
        if self._const:
            raise AttributeError("Cannot modify a const TravelExtendSettings object")
        self.cc_obj.search_interval = value

    @property
    def flight_start_day_time(self) -> DiffCostSettings:
        r = DiffCostSettings()
        r.cc_obj = self.cc_obj.flight_start_day_time
        r.const = True
        return r

    @flight_start_day_time.setter
    def flight_start_day_time(self, value: DiffCostSettings):
        if self._const:
            raise AttributeError("Cannot modify a const TravelExtendSettings object")
        self.cc_obj.flight_start_day_time = value.cc_obj

    @property
    def first_flight_wait_time(self) -> DiffCostSettings:
        return self._first_flight_wait_time

    @first_flight_wait_time.setter
    def first_flight_wait_time(self, value: DiffCostSettings):
        if self._const:
            raise AttributeError("Cannot modify a const TravelExtendSettings object")
        self.cc_obj.first_flight_wait_time = value.cc_obj

    @property
    def flight_wait_time(self) -> DiffCostSettings:
        r = DiffCostSettings()
        r.cc_obj = self.cc_obj.flight_start_day_time
        r.const = True
        return r

    @flight_wait_time.setter
    def flight_wait_time(self, value: DiffCostSettings):
        if self._const:
            raise AttributeError("Cannot modify a const TravelExtendSettings object")
        self.cc_obj.flight_wait_time = value.cc_obj

    @property
    def flight_duration(self) -> DiffCostSettings:
        r = DiffCostSettings()
        r.cc_obj = self.cc_obj.flight_wait_time
        r.const = True
        return r

    @flight_duration.setter
    def flight_duration(self, value: DiffCostSettings):
        if self._const:
            raise AttributeError("Cannot modify a const TravelExtendSettings object")
        self.cc_obj.flight_duration = value.cc_obj

    @property
    def cover_settings(self) -> TravelCoverSettings:
        r = TravelCoverSettings()
        r.cc_obj = self.cc_obj.cover_settings
        r.const = True
        return r

    @cover_settings.setter
    def cover_settings(self, value: TravelCoverSettings):
        if self._const:
            raise AttributeError("Cannot modify a const TravelExtendSettings object")
        self.cc_obj.cover_settings = value.cc_obj

    @property
    def move_cost(self) -> cost_t:
        return self.cc_obj.move_cost

    @move_cost.setter
    def move_cost(self, value: cost_t):
        if self._const:
            raise AttributeError("Cannot modify a const TravelExtendSettings object")
        self.cc_obj.move_cost = value

    def __repr__(self):
        return (
            f"TravelExtendSettings(\n"
            f"  day_scorer={self.day_scorer!r},\n"
            f"  search_interval={self.search_interval!r},\n"
            f"  flight_start_day_time={self.flight_start_day_time!r},\n"
            f"  first_flight_wait_time={self.first_flight_wait_time!r},\n"
            f"  flight_wait_time={self.flight_wait_time!r},\n"
            f"  flight_duration={self.flight_duration!r},\n"
            f"  cover_settings={self.cover_settings!r},\n"
            f"  move_cost={self.move_cost!r}\n)"
        )


cdef class TravelSearchSettings:
    cdef TravelSearchSettingsCC cc_obj
    cdef bool _const

    def __init__(
        self, *,
        day_scorer: DayScorer,
        search_interval: flight_duration_t,
        start_in_day_time: DiffCostSettings,
        start_out_day_time: DiffCostSettings,
        wait_time: DiffCostSettings,
        trip_duration: DiffCostSettings,
        flight_duration: DiffCostSettings,
        end_in_day_time: DiffCostSettings,
        end_out_day_time: DiffCostSettings,
        cover_settings: TravelCoverSettings,
        move_cost: cost_t,
        const_: bool = False
    ):

        self.cc_obj.day_scorer = day_scorer.cc_obj
        self.cc_obj.search_interval = search_interval
        self.cc_obj.start_in_day_time = start_in_day_time.cc_obj
        self.cc_obj.start_out_day_time = start_out_day_time.cc_obj
        self.cc_obj.wait_time = wait_time.cc_obj
        self.cc_obj.trip_duration = trip_duration.cc_obj
        self.cc_obj.flight_duration = flight_duration.cc_obj
        self.cc_obj.end_in_day_time = end_in_day_time.cc_obj
        self.cc_obj.end_out_day_time = end_out_day_time.cc_obj
        self.cc_obj.cover_settings = cover_settings.cc_obj
        self.cc_obj.move_cost = move_cost
        self._const = const_

    @property
    def const(self) -> bool:
        return self._const

    @const.setter
    def const(self, value: bool):
        if self._const and not value:
            raise ValueError("Cannot make a const object mutable!")
        self._const = value

    @property
    def day_scorer(self) -> DayScorer:
        r = DayScorer()
        r.cc_obj = self.cc_obj.day_scorer
        return r

    @day_scorer.setter
    def day_scorer(self, value: DayScorer):
        if self._const:
            raise AttributeError("Cannot modify a const TravelSearchSettings object")
        self.cc_obj.day_scorer = value.cc_obj

    @property
    def search_interval(self) -> flight_duration_t:
        return self.cc_obj.search_interval

    @search_interval.setter
    def search_interval(self, value: flight_duration_t):
        if self._const:
            raise AttributeError("Cannot modify a const TravelSearchSettings object")
        self.cc_obj.search_interval = value

    @property
    def start_in_day_time(self) -> DiffCostSettings:
        r = DiffCostSettings()
        r.cc_obj = self.cc_obj.start_in_day_time
        r.const = True
        return r

    @start_in_day_time.setter
    def start_in_day_time(self, value: DiffCostSettings):
        if self._const:
            raise AttributeError("Cannot modify a const TravelSearchSettings object")
        self.cc_obj.start_in_day_time = value.cc_obj

    @property
    def start_out_day_time(self) -> DiffCostSettings:
        r = DiffCostSettings()
        r.cc_obj = self.cc_obj.start_out_day_time
        r.const = True
        return r

    @start_out_day_time.setter
    def start_out_day_time(self, value: DiffCostSettings):
        if self._const:
            raise AttributeError("Cannot modify a const TravelSearchSettings object")
        self.cc_obj.start_out_day_time = value.cc_obj

    @property
    def wait_time(self) -> DiffCostSettings:
        r = DiffCostSettings()
        r.cc_obj = self.cc_obj.wait_time
        r.const = True
        return r

    @wait_time.setter
    def wait_time(self, value: DiffCostSettings):
        if self._const:
            raise AttributeError("Cannot modify a const TravelSearchSettings object")
        self.cc_obj.wait_time = value.cc_obj

    @property
    def trip_duration(self) -> DiffCostSettings:
        r = DiffCostSettings()
        r.cc_obj = self.cc_obj.trip_duration
        r.const = True
        return r

    @trip_duration.setter
    def trip_duration(self, value: DiffCostSettings):
        if self._const:
            raise AttributeError("Cannot modify a const TravelSearchSettings object")
        self.cc_obj.trip_duration = value.cc_obj

    @property
    def flight_duration(self) -> DiffCostSettings:
        r = DiffCostSettings()
        r.cc_obj = self.cc_obj.flight_duration
        r.const = True
        return r

    @flight_duration.setter
    def flight_duration(self, value: DiffCostSettings):
        if self._const:
            raise AttributeError("Cannot modify a const TravelSearchSettings object")
        self.cc_obj.flight_duration = value.cc_obj

    @property
    def end_in_day_time(self) -> DiffCostSettings:
        r = DiffCostSettings()
        r.cc_obj = self.cc_obj.end_in_day_time
        r.const = True
        return r

    @end_in_day_time.setter
    def end_in_day_time(self, value: DiffCostSettings):
        if self._const:
            raise AttributeError("Cannot modify a const TravelSearchSettings object")
        self.cc_obj.end_in_day_time = value.cc_obj

    @property
    def end_out_day_time(self) -> DiffCostSettings:
        r = DiffCostSettings()
        r.cc_obj = self.cc_obj.end_out_day_time
        r.const = True
        return r

    @end_out_day_time.setter
    def end_out_day_time(self, value: DiffCostSettings):
        if self._const:
            raise AttributeError("Cannot modify a const TravelSearchSettings object")
        self.cc_obj.end_out_day_time = value.cc_obj

    @property
    def cover_settings(self) -> TravelCoverSettings:
        r = TravelCoverSettings()
        r.cc_obj = self.cc_obj.cover_settings
        r.const = True
        return r

    @cover_settings.setter
    def cover_settings(self, value: TravelCoverSettings):
        if self._const:
            raise AttributeError("Cannot modify a const TravelSearchSettings object")
        self.cc_obj.cover_settings = value.cc_obj

    @property
    def move_cost(self) -> cost_t:
        return self.cc_obj.move_cost

    @move_cost.setter
    def move_cost(self, value: cost_t):
        if self._const:
            raise AttributeError("Cannot modify a const TravelSearchSettings object")
        self.cc_obj.move_cost = value

    def __repr__(self):
        return (
            f"TravelSearchSettings(\n"
            f"  day_scorer={self.day_scorer!r},\n"
            f"  search_interval={self.search_interval!r},\n"
            f"  start_in_day_time={self.start_in_day_time!r},\n"
            f"  start_out_day_time={self.start_out_day_time!r},\n"
            f"  wait_time={self.wait_time!r},\n"
            f"  trip_duration={self.trip_duration!r},\n"
            f"  flight_duration={self.flight_duration!r},\n"
            f"  end_in_day_time={self.end_in_day_time!r},\n"
            f"  end_out_day_time={self.end_out_day_time!r},\n"
            f"  cover_settings={self.cover_settings!r},\n"
            f"  move_cost={self.move_cost!r}\n)"
        )
