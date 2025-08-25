#include "optimizer.h"
#include "flight_structure.h"

#include <utility>
#include <set>
#include <algorithm>
#include <vector>
#include <iostream>


cost_t score_diff(const DiffCostSettings &settings, cost_t val) {
    cost_t diff_val = val - settings.desired_value;
    if (diff_val >= 0) {
        return diff_val * settings.up_factor;
    } else {
        return -diff_val * settings.down_factor;
    }
}

DayScorer compute_day_scores(
    const cost_t *day_costs, int ndays,
    flight_time_t start_time, flight_duration_t day_factor
) {
    DayScorer r = {
        .start_time = start_time,
        .day_factor = day_factor,
    };
    r.day_costs_agg.resize(ndays);
    cost_t score_sum = 0;
    for (int i=0; i<ndays; i++) {
        score_sum += day_costs[i];
        r.day_costs_agg[i] = score_sum;
    }
    return r;
}

cost_t compute_days_cost(
    const DayScorer &settings,
    flight_time_t start_time, flight_time_t end_time, bool continous = false
) {
    int nscores = settings.day_costs_agg.size();
    flight_time_t start_score, end_score;

    int start_pos = (start_time - settings.start_time) * settings.day_factor;
    if (!continous) {
        start_pos -= 1;
    }
    if (start_pos < 0) {
        start_score = 0;
    } else if (start_pos >= nscores) {
        start_score = settings.day_costs_agg[nscores-1];
    } else {
        start_score = settings.day_costs_agg[start_pos];
    }
    int end_pos = (end_time - settings.start_time) * settings.day_factor;
    if (end_pos < 0) {
        end_score = 0;
    } else if (end_pos >= nscores) {
        end_score = settings.day_costs_agg[nscores-1];
    } else {
        end_score = settings.day_costs_agg[end_pos];
    }

    return end_score - start_score;
}

FlightTravel extend_travel(
    const FlightTravel &travel, const Flight &flight,
    const DayScorer &day_settings,
    cost_t move_cost,
    const DiffCostSettings &wait_time_scoring,
    const DiffCostSettings &flight_start_scoring,
    const DiffCostSettings &flight_duration_scoring
) {
    auto cost = travel.cost + flight.cost;
    cost += compute_days_cost(
        day_settings, travel.end_time,
        flight.start_time + flight.duration, travel.flights_count
    );
    if (travel.flights_count) {
        cost += move_cost + score_diff(wait_time_scoring, flight.start_time - travel.end_time);
    }
    cost += score_diff(flight_start_scoring, flight.day_start_time);
    cost += score_diff(flight_duration_scoring, flight.duration);
    return {
        .last_flight = flight.id,
        .last_travel = travel.id,
        .flights_count = travel.flights_count+1,
        .end_time = flight.start_time + flight.duration,
        .day_end_time = flight.day_end_time,
        .cost = cost,
        .end_vertex = flight.dst,
    };
}

FlightTravel extend_best_travel(
    const std::vector<FlightTravel> &travel_vec, const Flight &flight, flight_duration_t search_intervel,
    const DayScorer &day_settings,
    cost_t move_cost,
    const DiffCostSettings &wait_time_scoring,
    const DiffCostSettings &flight_start_scoring,
    const DiffCostSettings &flight_duration_scoring,
    int min_check_flights=8
) {
    FlightTravel search_travel;
    search_travel.end_time = flight.start_time - wait_time_scoring.desired_value - search_intervel;
    auto it = std::lower_bound(travel_vec.begin(), travel_vec.end(), search_travel, TravelCompareTime());
    search_travel.end_time = std::min(
        flight.start_time - wait_time_scoring.desired_value + search_intervel, flight.start_time
    );
    auto it_end = std::upper_bound(travel_vec.begin(), travel_vec.end(), search_travel, TravelCompareTime());
    if (it_end - it < min_check_flights) { // select at least min_check_fligths if possible
        it = std::max(it_end - min_check_flights, travel_vec.begin());
    }

    FlightTravel best_travel;
    best_travel.cost = 1e9;
    for (; it != it_end; ++it) {
        const auto &travel = *it;
        if (travel.end_vertex != flight.src || travel.end_time > flight.start_time) {
            continue;
        }

        auto cost = travel.cost + flight.cost;
        cost += compute_days_cost(
            day_settings, travel.end_time,
            flight.start_time + flight.duration, travel.flights_count
        );
        if (travel.flights_count) {
            cost += move_cost + score_diff(wait_time_scoring, travel.end_time);
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
                .day_end_time = flight.day_end_time,
                .cost = cost,
                .end_vertex = flight.dst,
            };
        }
    }

    return best_travel;
}

bool push_travel(
    std::vector<FlightTravel> &travel_vec, const FlightTravel &new_travel,
    const TravelCoverSettings &settings
) {
    auto search_end_time = new_travel.end_time - settings.time_back;

    // Check if travel is covered by another
    for (auto it = travel_vec.rbegin(); it != travel_vec.rend(); ++it) {
        auto travel = *it;
        if (travel.end_time < search_end_time) {
            break;
        }

        auto time_diff = new_travel.end_time - travel.end_time;
        auto cost_diff = new_travel.cost - travel.cost;

        if (time_diff > 0) {
            if (cost_diff < -time_diff * settings.back_cost_factor) {
                return false;
            }
        } else {
            if (cost_diff < time_diff * settings.forward_cost_factor) {
                return false;
            }
        }
        ++it;
    }

    // Remove travels this one covers
    while (!travel_vec.empty()) {
        auto travel = travel_vec.back();
        auto time_diff = new_travel.end_time - travel.end_time;
        auto cost_diff = new_travel.cost - travel.cost;

        if (time_diff > 0) {
            if (cost_diff > time_diff * settings.back_cost_factor) {
                travel_vec.pop_back();
                continue;
            }
        } else {
            if (cost_diff > -time_diff * settings.forward_cost_factor) {
                travel_vec.pop_back();
                continue;
            }
        }
        break;
    }

    // Insert travel
    travel_vec.push_back(new_travel);
    return true;
}

auto extend_travels(
    const std::map<vertex_t, std::vector<FlightTravel>> &travels_mapping,
    const std::vector<Flight> &flights, const TravelExtendSettings &settings,
    travel_t &travel_id_inc
) {
    std::vector<Flight> flights_by_time = flights;
    std::sort(flights_by_time.begin(), flights_by_time.end(), FlightCompareTime());

    std::vector<FlightTravel> created_travels;
    std::map<vertex_t, std::vector<FlightTravel>> new_travels_by_city;
    for (const auto &flight : flights_by_time) {
        const auto travels_it_in = travels_mapping.find(flight.src);
        if (travels_it_in != travels_mapping.end()) {
            const auto &travels = travels_it_in->second;
            auto new_travel_in = extend_best_travel(
                travels, flight, settings.search_interval,
                settings.day_scorer, settings.move_cost, settings.first_flight_wait_time,
                settings.flight_start_day_time,
                settings.flight_duration
            );
            if (new_travel_in.cost >= 1e8) {
                continue;
            }
            new_travel_in.id = travel_id_inc;
            if (push_travel(
                new_travels_by_city[flight.dst], new_travel_in, settings.cover_settings
            )) {
                created_travels.push_back(new_travel_in);
                ++travel_id_inc;
            }
        }

        const auto travels_it_comp = new_travels_by_city.find(flight.src);
        if (travels_it_comp != new_travels_by_city.end()) {
            const auto &travels = travels_it_comp->second;
            auto new_travel_comp = extend_best_travel(
                travels, flight, settings.search_interval,
                settings.day_scorer, settings.move_cost, settings.flight_wait_time,
                zero_cost,
                settings.flight_duration
            );
            if (new_travel_comp.cost >= 1e8) {
                continue;
            }
            new_travel_comp.id = travel_id_inc;
            if (push_travel(
                new_travels_by_city[flight.dst], new_travel_comp, settings.cover_settings
            )) {
                created_travels.push_back(new_travel_comp);
                ++travel_id_inc;
            }
        }
    }

    return std::pair(new_travels_by_city, created_travels);
}

std::set<travel_t> select_used_travels(
    const std::map<travel_t, FlightTravel> &all_travels,
    const std::vector<FlightTravel> &selected_travels
) {
    std::set<travel_t> used_travels;
    for (const auto &travel : selected_travels) {
        travel_t travel_id = travel.id;
        used_travels.insert(travel_id);
        auto travel_it = all_travels.find(travel_id);
        while (travel_it != all_travels.end()) {
            travel_id = travel_it->second.last_travel;
            used_travels.insert(travel_id);
            travel_it = all_travels.find(travel_id);
        }
    }
    return used_travels;
}

void normalize_travel_ids(std::vector<FlightTravel> &travels) {
    std::map<travel_t, travel_t> travel_map;
    for (int it=0; it<travels.size(); ++it) {
        auto &travel = travels[it];
        travel_map[travel.id] = it;
        travel.id = it;
        if (travel.last_travel >= 0) {
            travel.last_travel = travel_map[travel.last_travel];
        }
    }
}

std::vector<FlightTravel> find_best_single_trip(
    vertex_t start_city, flight_time_t start_time,
    const std::vector<Flight> &flights,
    const TravelSearchSettings &settings,
    const std::map<vertex_t, cost_t> &city_costs
) {
    travel_t travel_id_inc = 0;
    FlightTravel start_travel = {
        .id = travel_id_inc++,
        .last_flight = -1,
        .last_travel = -1,
        .flights_count = 0,
        .end_time = start_time,
        .cost = 0,
        .end_vertex = start_city,
    };

    std::map<travel_t, FlightTravel> all_travels = {
        {start_travel.id, start_travel},
    };
    std::map<vertex_t, std::vector<FlightTravel>> start_trip;
    start_trip[start_city].push_back(start_travel);
    TravelExtendSettings start_extend_settings = {
        .day_scorer = settings.day_scorer,
        .search_interval = settings.search_interval,
        .flight_start_day_time = settings.start_in_day_time,
        .first_flight_wait_time = zero_cost,
        .flight_wait_time = settings.wait_time,
        .flight_duration = settings.flight_duration,
        .cover_settings = settings.cover_settings,
        .move_cost = settings.move_cost,
    };
    auto [to_city_travels, new_travels_to] = extend_travels(start_trip, flights, start_extend_settings, travel_id_inc);
    for (auto &city_travels : to_city_travels) {
        for (auto &travel : city_travels.second) {
            auto cost_it = city_costs.find(travel.end_vertex);
            if (cost_it != city_costs.end()) {
                travel.cost += cost_it->second;
            }
            travel.cost += score_diff(settings.start_out_day_time, travel.day_end_time);
        }
    }
    for (auto travel : new_travels_to) {
        auto cost_it = city_costs.find(travel.end_vertex);
        if (cost_it != city_costs.end()) {
            travel.cost += cost_it->second;
        }
        travel.cost += score_diff(settings.start_out_day_time, travel.day_end_time);

        all_travels[travel.id] = travel;
    }

    TravelExtendSettings end_extend_settings = {
        .day_scorer = settings.day_scorer,
        .search_interval = settings.search_interval,
        .flight_start_day_time = settings.end_in_day_time,
        .first_flight_wait_time = settings.trip_duration,
        .flight_wait_time = settings.wait_time,
        .flight_duration = settings.flight_duration,
        .cover_settings = settings.cover_settings,
        .move_cost = settings.move_cost,
    };
    auto [from_city_travels, new_travels_from] = extend_travels(to_city_travels, flights, end_extend_settings, travel_id_inc);
    for (auto &city_travels : from_city_travels) {
        for (auto &travel : city_travels.second) {
            travel.cost += score_diff(settings.end_out_day_time, travel.day_end_time);
        }
    }
    for (auto travel : new_travels_from) {
        travel.cost += score_diff(settings.end_out_day_time, travel.day_end_time);
        all_travels[travel.id] = travel;
    }

    std::vector<FlightTravel> res_travels;
    for (auto travel_id : select_used_travels(all_travels, new_travels_to)) {
        res_travels.push_back(all_travels[travel_id]);
    }
    normalize_travel_ids(res_travels);
    return res_travels;
}
