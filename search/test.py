from search_flights.flight_optim import (
    TravelSearchSettings, DiffCostSettings, TravelCoverSettings,
    FlightIndex, DayScorer,
    find_best_single_trip
)


city_0 = 0
city_1 = 1
city_2 = 2
city_3 = 3


def make_test_index():
    idx = FlightIndex()
    idx.push_flight(0, city_0, city_1, .5, .5, .25, 10)
    idx.push_flight(1, city_0, city_1, 1.5, .5, .2, 20)
    idx.push_flight(2, city_1, city_0, 2.5, .5, .15, 30)
    idx.push_flight(3, city_1, city_0, 3.5, .5, .2, 40)
    idx.sort_flights()
    return idx


idx = make_test_index()
day_scorer = DayScorer((1, 2, 3, 4), start_time=.01)
print(day_scorer)

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
    cover_settings=TravelCoverSettings(back_cost_factor=1., forward_cost_factor=1., time_back=7.),
    move_cost=100.
)

city_costs = {
    city_0: 10,
    city_1: 100,
    city_2: 1000,
    city_3: 10000
}

print(settings)
print(idx.select_flights((city_0, city_1), (city_0, city_1), 0, 1000000))
print(find_best_single_trip(
    city_0, 0.,
    flights=idx.select_flights((city_0, city_1), (city_0, city_1), 0, 1000000),
    settings=settings,
    city_costs=city_costs
))