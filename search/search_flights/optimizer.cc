#include "optimizer.h"
#include "flight_structure.h"

#include <map>
#include <algorithm>

cost_t score_diff(const DiffCostSettings &settings, cost_t val) {
    cost_t diff_val = val - settings.desired_value;
    if (diff_val >= 0) {
        return diff_val * settings.up_factor;
    } else {
        return -diff_val * settings.down_factor;
    }
}

FlightTravel extend_travel(
    const FlightTravel &travel, const Flight &flight,
    const DiffCostSettings &wait_time_scoring,
    const DiffCostSettings &flight_start_scoring,
    const DiffCostSettings &flight_end_scoring,
    const DiffCostSettings &flight_duration_scoring
) {
    auto cost = travel.cost;
    if (travel.flights_count) {
        cost += score_diff(wait_time_scoring, travel.end_time);
    }
    cost += score_diff(flight_start_scoring, flight.day_start_time);
    cost += score_diff(flight_duration_scoring, flight.duration);
    return {
        .last_flight = flight.id,
        .last_travel = travel.id,
        .flights_count = travel.flights_count+1,
        .end_time = flight.start_time + flight.duration,
        .cost = cost,
        .end_vertex = flight.dst,
    };
}

template<class Ts>
FlightTravel extend_best_travel(
    const Ts &travel_set, const Flight &flight, flight_duration_t search_intervel,
    const DiffCostSettings &wait_time_scoring,
    const DiffCostSettings &flight_start_scoring,
    const DiffCostSettings &flight_end_scoring,
    const DiffCostSettings &flight_duration_scoring
) {
    FlightTravel search_start_travel, search_end_travel;
    search_start_travel.end_time = flight.start_time - wait_time_scoring.desired_value - search_intervel;
    auto it = travel_set.lower_bound(search_start_travel);
    search_end_travel.end_time = std::min(
        flight.start_time - wait_time_scoring.desired_value + search_intervel, flight.start_time
    );
    auto it_end = travel_set.upper_bound(search_end_travel);

    FlightTravel best_travel;
    best_travel.cost = 1e9;
    for (; it != it_end; ++it) {
        const auto &travel = *it;
        auto cost = travel.cost;
        if (travel.flights_count) {
            cost += score_diff(wait_time_scoring, travel.end_time);
        }
        cost += score_diff(flight_start_scoring, flight.day_start_time);
        cost += score_diff(flight_duration_scoring, flight.duration);
        if (cost < best_travel.cost) {
            best_travel = {
                .id = 0,
                .last_flight = flight.id,
                .last_travel = travel.id,
                .flights_count = travel.flights_count+1,
                .end_time = flight.start_time + flight.duration,
                .cost = cost,
                .end_vertex = flight.dst,
            };
        }
    }

    return best_travel;
}

template<class Ts>
void push_travel(
    Ts &travel_set, const FlightTravel &new_travel,
    cost_t back_cost_factor, cost_t forward_cost_factor,
    flight_duration_t time_back
) {
    FlightTravel search_travel = new_travel;
    search_travel.end_time -= time_back;

    // Check if travel is covered by another
    auto it = travel_set.lower_bound(search_travel);
    while (it != travel_set.end()) {
        auto travel = *it;
        auto time_diff = new_travel.end_time - travel.end_time;
        auto cost_diff = new_travel.cost - travel.cost;

        if (time_diff > 0) {
            if (cost_diff < -time_diff * back_cost_factor) {
                return;
            }
        } else {
            if (cost_diff < time_diff * forward_cost_factor) {
                return;
            }
        }
        ++it;
    }

    // Remove travels this one convers
    it = travel_set.lower_bound(search_travel);
    while (it != travel_set.end()) {
        auto travel = *it;
        auto time_diff = new_travel.end_time - travel.end_time;
        auto cost_diff = new_travel.cost - travel.cost;

        if (time_diff > 0) {
            if (cost_diff > time_diff * back_cost_factor) {
                it = travel_set.erase(it);
                continue;
            }
        } else {
            if (cost_diff > -time_diff * forward_cost_factor) {
                it = travel_set.erase(it);
                continue;
            }
        }
        ++it;
    }

    // Insert travel
    travel_set.insert(new_travel);
}
