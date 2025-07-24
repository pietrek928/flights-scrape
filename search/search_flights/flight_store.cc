#include "flight_store.h"

#include <algorithm>
#include <stdexcept>


void FlightIndex::push_flight(
    flight_t id, vertex_t src, vertex_t dst,
    flight_time_t start_time, flight_time_t day_start_time,
    flight_duration_t duration, cost_t cost
) {
    sorted = false;
    flights.push_back({
        .id = id, .src = src, .dst = dst,
        .start_time = start_time, .day_start_time = day_start_time,
        .duration = duration, .cost = cost,
    });
}

void FlightIndex::sort_flights() {
    if (!sorted) {
        std::sort(flights.begin(), flights.end(), FlightCompareVertex());
        sorted = true;
    }
}

std::vector<Flight> FlightIndex::select_flights(
    const vertex_t *src_vs, int nsrc_v,
    const vertex_t *dst_vs, int ndst_v,
    flight_time_t start_time, flight_time_t end_time
) const {
    if (!sorted) {
        throw std::invalid_argument("Flights set must be sorted");
    }

    std::vector<Flight> out;
    Flight search_flight;
    for (int i=0; i<nsrc_v; i++) {
        search_flight.src = src_vs[i];
        for (int j=0; j<ndst_v; j++) {
            search_flight.dst = dst_vs[j];
            search_flight.start_time = start_time;
            auto start = std::lower_bound(
                flights.begin(), flights.end(), search_flight, FlightCompareVertex()
            );
            search_flight.start_time = end_time;
            auto end = std::upper_bound(
                flights.begin(), flights.end(), search_flight, FlightCompareVertex()
            );
            out.reserve(out.size() + std::distance(start, end));
            out.insert(out.end(), start, end);
        }
    }
    return out;
}
