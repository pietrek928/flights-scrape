#pragma once


typedef float flight_time_t;
typedef float flight_duration_t;
typedef float cost_t;

typedef int vertex_t;
typedef int flight_t;
typedef int travel_t;
constexpr static int edge_pos_none = -1;

typedef struct Flight {
  flight_t id = 0;
  vertex_t src = 0;
  vertex_t dst = 0;
  flight_time_t start_time = 0;
  flight_time_t day_start_time = 0;
  flight_time_t day_end_time = 0;
  flight_duration_t duration = 0;
  cost_t cost = 0;
} Flight;

typedef struct FlightTravel {
  travel_t id = 0;
  flight_t last_flight = 0;
  travel_t last_travel = 0;
  int flights_count = 0;

  flight_time_t end_time = 0;
  flight_time_t day_end_time = 0;
  cost_t cost = 0;
  vertex_t end_vertex = 0;
} FlightTravel;
