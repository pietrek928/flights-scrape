#pragma once


typedef float flight_time_t;
typedef float flight_duration_t;
typedef float cost_t;

typedef int vertex_t;
typedef int flight_t;
typedef int travel_t;
constexpr static int edge_pos_none = -1;

typedef struct {
    flight_t id;
    vertex_t src;
    vertex_t dst;
    flight_time_t start_time;
    flight_time_t day_start_time;
    flight_duration_t duration;
    cost_t cost;
} Flight;

typedef struct {
    flight_t id;
    flight_t last_flight;
    travel_t last_travel;
    int flights_count;

    flight_time_t end_time;
    flight_time_t day_end_time;
    cost_t cost;
    vertex_t end_vertex;
} FlightTravel;
