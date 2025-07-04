from libcpp.vector cimport vector

cdef extern from "flight_structure.h":
    cdef cppclass Flight:
        pass

cdef extern from "flight_store.h"
    cdef cppclass FlightIndex "FlightIndexCC":
        FlightIndex(const vector[Flight] init_flights)
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

cdef class FlightsList:
    cdef vector[Flight] flights


