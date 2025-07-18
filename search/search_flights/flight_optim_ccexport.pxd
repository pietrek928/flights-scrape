from libcpp.vector cimport vector


cdef extern from "flight_structure.h":
    ctypedef float flight_time_t
    ctypedef float flight_duration_t
    ctypedef float cost_t
    ctypedef int vertex_t
    ctypedef int flight_t
    ctypedef int travel_t

    cdef cppclass Flight:
        pass


cdef extern from "flight_store.cc":
    cdef cppclass FlightIndex:
        FlightIndex()
        FlightIndex(const vector[Flight] &init_flights)
        void push_flight(
            flight_t id, vertex_t src, vertex_t dst,
            flight_time_t start_time, flight_time_t day_start_time,
            flight_duration_t duration
        )
        void sort_flights()
        vector[Flight] select_flights(
            const vertex_t *src_vs, int nsrc_v,
            const vertex_t *dst_vs, int ndst_v,
            flight_time_t start_time, flight_time_t end_time
        ) const


cdef extern from "optimizer.cc":
    ctypedef struct DiffCostSettings:
        cost_t desired_value
        cost_t down_factor
        cost_t up_factor

    ctypedef struct DayScorer:
        pass

    ctypedef struct TravelCoverSettings:
        cost_t back_cost_factor
        cost_t forward_cost_factor
        flight_duration_t time_back

    ctypedef struct TravelExtendSettings:
        DayScorer day_scorer
        flight_duration_t search_interval
        DiffCostSettings flight_start_day_time
        DiffCostSettings first_flight_wait_time
        DiffCostSettings flight_wait_time
        DiffCostSettings flight_duration
        TravelCoverSettings cover_settings
        cost_t move_cost

    ctypedef struct TravelSearchSettings:
        DayScorer day_scorer
        flight_duration_t search_interval
        DiffCostSettings start_in_day_time
        DiffCostSettings start_out_day_time
        DiffCostSettings wait_time
        DiffCostSettings trip_duration
        DiffCostSettings flight_duration
        DiffCostSettings end_in_day_time
        DiffCostSettings end_out_day_time
        TravelCoverSettings cover_settings
        cost_t move_cost

    cdef DayScorer compute_day_scores(
        const cost_t *day_costs, int ndays,
        flight_time_t start_time, flight_duration_t day_factor
    )
