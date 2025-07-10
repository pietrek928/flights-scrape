from libcpp.vector cimport vector
from .flight_optim_ccexport cimport (
    Flight as FlightCC, FlightIndex as FlightIndexCC,
    flight_t, vertex_t, flight_time_t, flight_duration_t
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
