from collections import defaultdict
import os
import json
import lzma as xz
from datetime import datetime, timedelta

from .flight_optim import (
    TravelSearchSettings, DiffCostSettings, TravelCoverSettings,
    FlightIndex, DayScorer,
    find_best_single_trip
)


def _date_to_days(date_str, date_base):
    target_parsed = datetime.fromisoformat(date_str.replace("Z", ""))
    return (target_parsed - date_base).total_seconds() / 86400


def _get_day_time(date_str):
    date_parsed = datetime.fromisoformat(date_str.replace("Z", ""))
    return timedelta(
        hours=date_parsed.hour, minutes=date_parsed.minute, seconds=date_parsed.second
    ).total_seconds() / 86400


def _city_to_num(idx, code):
    if code in idx:
        return idx[code]
    else:
        idx[code] = len(idx)
        return idx[code]

def flight_id_to_int(flight_id):
    clean_id = flight_id.replace(' ', '').upper()
    return int(clean_id[:2], 36) * int(1e4) + int(clean_id[2:],)


# def int_to_flight_id(numeric_id):
#     return (
#         np.base_repr(numeric_id // int(1e6), 36).upper()
#         + f'{numeric_id % int(1e6):04d}'
#     )


def load_ryanair_flights(root_dir):
    city_idx = {}
    flights = FlightIndex()
    flight_id_idx = defaultdict(int)
    date_base = datetime(2025, 1, 1)

    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.json.xz'):
                file_path = os.path.join(root, file)
                with xz.open(file_path, 'rt', encoding='utf-8') as f:
                    data = json.load(f)
                    for t in data['booking']['trips'][0]['dates']:
                        for f in t['flights']:
                            if f.get('regularFare'):
                                flight_id = flight_id_to_int(f['flightNumber'])
                                flight_id_idx[flight_id] += 1
                                flight_id = flight_id * 100 + flight_id_idx[flight_id]

                                src = _city_to_num(city_idx, f['segments'][0]['origin'])
                                dst = _city_to_num(city_idx, f['segments'][0]['destination'])
                                date_start, date_end = f['timeUTC']
                                date_start = _date_to_days(date_start, date_base)
                                date_end = _date_to_days(date_end, date_base)
                                day_start_time = _get_day_time(f['time'][0])
                                day_end_time = _get_day_time(f['time'][1])
                                price = f['regularFare']['fares'][0]['publishedFare']
                                # print(flight_id, src, '->', dst, (date_end - date_start) * 24, f['segments'][0]['duration'], price)
                                flights.push_flight(
                                    id=flight_id, src=src, dst=dst,
                                    start_time=date_start, day_start_time=day_start_time,
                                    day_end_time=day_end_time,
                                    duration=date_end - date_start, cost=price
                                )
    return flights, city_idx


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

    # TODO: fix wait time cost between flight forth and back
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
