#pragma once
#include "flight_structure.h"

#include <vector>


struct FlightCompareTime {
    inline bool operator()(const Flight& a, const Flight& b) const {
        return a.start_time < b.start_time;
    }
};

typedef struct {
    cost_t desired_value;
    cost_t down_factor;
    cost_t up_factor;
} DiffCostSettings;

typedef struct {
    flight_time_t start_time;
    flight_duration_t day_factor;
    std::vector<cost_t> day_costs_agg;
} DayScorer;

typedef struct {
    DayScorer day_scorer;
    DiffCostSettings start_in_day_time, start_out_day_time;
    DiffCostSettings trip_duration;
    DiffCostSettings end_in_day_time, end_out_day_time;
} TravelSearchSettings;
