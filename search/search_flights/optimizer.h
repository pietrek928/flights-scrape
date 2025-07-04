#pragma once
#include "flight_structure.h"


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
    DiffCostSettings start_in_day_time, start_out_day_time;
    DiffCostSettings trip_duration;
    DiffCostSettings end_in_day_time, end_out_day_time;
} TripSearchSettings;
