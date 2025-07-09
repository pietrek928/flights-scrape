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
