from libcpp.vector cimport vector
from .flight_optim_ccexport cimport (
    Flight as FlightCC, FlightIndex as FlightIndexCC,
    flight_t, vertex_t, flight_time_t, flight_duration_t
)


cdef class FlightsList:
    cdef vector[FlightCC] flights


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
