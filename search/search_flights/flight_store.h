#include "flight_structure.h"
#include <vector>


struct FlightCompareVertex {
    inline bool operator()(const Flight& a, const Flight& b) const {
        if (a.src != b.src) {
            return a.src < b.src;
        }
        if (a.dst != b.dst) {
            return a.dst < b.dst;
        }
        return a.start_time + a.duration < b.start_time + b.duration;
    }
};

class FlightIndex {
    std::vector<Flight> flights;
    bool sorted = false;

    public:

    FlightIndex() {}
    FlightIndex(const std::vector<Flight> &init_flights)
        : flights(init_flights.begin(), init_flights.end()) {}
    void push_flight(
        flight_t id, vertex_t src, vertex_t dst,
        flight_time_t start_time, flight_time_t day_start_time,
        flight_duration_t duration, cost_t cost
    );
    void sort_flights();
    std::vector<Flight> select_flights(
        const vertex_t *src_vs, int nsrc_v,
        const vertex_t *dst_vs, int ndst_v,
        flight_time_t start_time, flight_time_t end_time
    ) const;
    inline auto size() {
        return flights.size();
    }
};
