from collections import defaultdict
from datetime import UTC, datetime

from .load_flights import city_to_num, load_ryanair_flights, load_wizzair_flights
from .flight_optim import (
    TravelSearchSettings, DiffCostSettings, TravelCoverSettings,
    FlightIndex, DayScorer,
    find_best_single_trip
)


def find_flights():
    flights = FlightIndex()
    datetime_base = datetime.now(UTC)
    city_idx = {}
    flight_id_idx = defaultdict(int)
    # load_ryanair_flights(
    #     flights, 'data/ryanair', datetime_base,
    #     city_idx, flight_id_idx
    # )
    load_wizzair_flights(
        flights, 'data/wizzair', datetime_base,
        city_idx, flight_id_idx
    )
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
        {city_to_num(city_idx, 'WAW'), city_to_num(city_idx, 'ALC')},
        {city_to_num(city_idx, 'WAW'), city_to_num(city_idx, 'ALC')},
        0, 1000000
    )
    print(selected_flights)

    start_city_idx = city_to_num(city_idx, 'WAW')
    print('start city', start_city_idx)
    trips = find_best_single_trip(
        city_to_num(city_idx, 'WAW'), 0.,
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
