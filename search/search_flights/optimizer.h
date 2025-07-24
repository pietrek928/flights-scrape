#pragma once
#include "flight_structure.h"

#include <vector>
#include <map>


struct FlightCompareTime {
    inline bool operator()(const Flight& a, const Flight& b) const {
        return a.start_time + a.duration < b.start_time + b.duration;
    }
};

struct TravelCompareTime {
    inline bool operator()(const FlightTravel& a, const FlightTravel& b) const {
        return a.end_time < b.end_time;
    }
};

typedef struct {
    cost_t desired_value;
    cost_t down_factor;
    cost_t up_factor;
} DiffCostSettings;

constexpr static DiffCostSettings zero_cost = {
    .desired_value = 0,
    .down_factor = 0,
    .up_factor = 0,
};

typedef struct {
    flight_time_t start_time;
    flight_duration_t day_factor;
    std::vector<cost_t> day_costs_agg;
} DayScorer;

typedef struct {
    cost_t back_cost_factor;
    cost_t forward_cost_factor;
    flight_duration_t time_back;
} TravelCoverSettings;

typedef struct {
    DayScorer day_scorer;
    flight_duration_t search_interval;
    DiffCostSettings flight_start_day_time;
    DiffCostSettings first_flight_wait_time, flight_wait_time, flight_duration;
    TravelCoverSettings cover_settings;
    cost_t move_cost;
} TravelExtendSettings;

typedef struct {
    DayScorer day_scorer;
    flight_duration_t search_interval;
    DiffCostSettings start_in_day_time, start_out_day_time;
    DiffCostSettings end_in_day_time, end_out_day_time;
    DiffCostSettings wait_time, trip_duration, flight_duration;
    TravelCoverSettings cover_settings;
    cost_t move_cost;
} TravelSearchSettings;


DayScorer compute_day_scores(
    const cost_t *day_costs, int ndays,
    flight_time_t start_time, flight_duration_t day_factor
);

std::vector<FlightTravel> find_best_single_trip(
    vertex_t start_city, flight_time_t start_time,
    const std::vector<Flight> &flights,
    const TravelSearchSettings &settings,
    const std::map<vertex_t, cost_t> &city_costs
);
