from collections import defaultdict
import os
import json
import lzma as xz
from datetime import datetime, timedelta
from typing import Dict

from .flight_optim import (
    TravelSearchSettings, DiffCostSettings, TravelCoverSettings,
    FlightIndex, DayScorer,
    find_best_single_trip
)



def find_flights():
    flights, city_idx = load_ryanair_flights('/run/media/pietrek/C068DF4C68DF4038/data/datasets/ryanair')
    flights.sort_flights()
    # for f in iter(flights):
    #     print(f)

    day_scorer = DayScorer((1, 2, 3, 4), start_time=.01)
    city_costs = {}

    settings = TravelSearchSettings(
        day_scorer=day_scorer,
        search_interval=3.,
        start_in_day_time=DiffCostSettings(desired_value=8/24, down_factor=5., up_factor=5.),
        start_out_day_time=DiffCostSettings(desired_value=12/24, down_factor=5., up_factor=5.),
        end_in_day_time=DiffCostSettings(desired_value=18/24, down_factor=5., up_factor=5.),
        end_out_day_time=DiffCostSettings(desired_value=20/24, down_factor=5., up_factor=5.),
        wait_time=DiffCostSettings(desired_value=2/24, down_factor=30., up_factor=5.),
        trip_duration=DiffCostSettings(desired_value=2., down_factor=10., up_factor=10.),
        flight_duration=DiffCostSettings(desired_value=3., down_factor=.01, up_factor=1.),
        cover_settings=TravelCoverSettings(back_cost_factor=100., forward_cost_factor=100., time_back=7.),
        move_cost=100.
    )

    selected_flights = flights.select_flights(
        {_city_to_num(city_idx, 'WAW'), _city_to_num(city_idx, 'ALC')},
        {_city_to_num(city_idx, 'WAW'), _city_to_num(city_idx, 'ALC')},
        0, 1000000
    )
    print(selected_flights)

    start_city_idx = _city_to_num(city_idx, 'WAW')
    print('start city', start_city_idx)
    trips = find_best_single_trip(
        _city_to_num(city_idx, 'WAW'), 0.,
        flights=selected_flights,
        settings=settings,
        city_costs=city_costs
    )
    print(len(trips))
    for t in trips:
        print(t)
    # trips.show()


if __name__ == '__main__':
    find_flights()
