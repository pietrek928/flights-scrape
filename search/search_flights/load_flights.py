from collections import defaultdict
import os
import json
import lzma as xz
import logging
from datetime import UTC, datetime, timedelta
from typing import Dict

from .flight_optim import FlightIndex


def iterate_json_xz(root_dir: str):
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.json.xz'):
                file_path = os.path.join(root, file)
                with xz.open(file_path, 'rt', encoding='utf-8') as f:
                    yield json.load(f)


def date_to_days(date_str, date_base):
    target_parsed = datetime.fromisoformat(date_str.replace("Z", "")).replace(tzinfo=UTC)
    return (target_parsed - date_base).total_seconds() / 86400


def _parse_time(time_str):
    h, m, s = time_str.split(':')
    return timedelta(hours=int(h), minutes=int(m), seconds=int(s)).total_seconds() / 86400


def get_day_time(date_str):
    date_parsed = datetime.fromisoformat(date_str.replace("Z", ""))
    return timedelta(
        hours=date_parsed.hour, minutes=date_parsed.minute, seconds=date_parsed.second
    ).total_seconds() / 86400


def city_to_num(idx, code):
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


def load_ryanair_flights(
    flights: FlightIndex, root_dir, datetime_base,
    city_idx: Dict, flight_id_idx: defaultdict[int]
):
    for data in iterate_json_xz(root_dir):
        for t in data['booking']['trips'][0]['dates']:
            for f in t['flights']:
                if f.get('regularFare'):
                    flight_id = flight_id_to_int(f['flightNumber'])
                    flight_id_idx[flight_id] += 1
                    flight_id = flight_id * 100 + flight_id_idx[flight_id]

                    src = city_to_num(city_idx, f['segments'][0]['origin'])
                    dst = city_to_num(city_idx, f['segments'][0]['destination'])
                    date_start, date_end = f['timeUTC']
                    date_start = date_to_days(date_start, datetime_base)
                    date_end = date_to_days(date_end, datetime_base)
                    day_start_time = get_day_time(f['time'][0])
                    day_end_time = get_day_time(f['time'][1])
                    price = f['regularFare']['fares'][0]['publishedFare']
                    # print(flight_id, src, '->', dst, (date_end - date_start) * 24, f['segments'][0]['duration'], price)
                    flights.push_flight(
                        id=flight_id, src=src, dst=dst,
                        start_time=date_start, day_start_time=day_start_time,
                        day_end_time=day_end_time,
                        duration=date_end - date_start, cost=price
                    )


def _get_wizzair_prices(fares):
    prices = {}
    for fare in fares:
        if fare.get('bundle') and fare.get('fullBasePrice'):
            prices[fare['bundle']] = fare['fullBasePrice']['amount']
    return prices


def load_wizzair_flights(
    flights: FlightIndex, root_dir, datetime_base,
    city_idx: Dict, flight_id_idx: defaultdict[int]
):
    for data in iterate_json_xz(root_dir):
        if data['body'].get('outboundFlights'):
            for flight in data['body']['outboundFlights']:
                flight_id = flight_id_to_int(flight['carrierCode'] + flight['flightNumber'])
                flight_id_idx[flight_id] += 1
                flight_id = flight_id * 100 + flight_id_idx[flight_id]

                src = city_to_num(city_idx, flight['departureStation'])
                dst = city_to_num(city_idx, flight['arrivalStation'])
                date_start = date_to_days(flight['departureDateTime'], datetime_base) - _parse_time(flight['departureTimeUtcOffset'])
                date_end = date_to_days(flight['arrivalDateTime'], datetime_base) - _parse_time(flight['arrivalTimeUtcOffset'])
                day_start_time = get_day_time(flight['departureDateTime'])
                day_end_time = get_day_time(flight['arrivalDateTime'])
                prices = _get_wizzair_prices(flight['fares'])
                print(flight_id, src, '->', dst, 'prices', prices)

                if prices:
                    flights.push_flight(
                        id=flight_id, src=src, dst=dst,
                        start_time=date_start, day_start_time=day_start_time,
                        day_end_time=day_end_time,
                        duration=date_end - date_start, cost=prices['basic']
                    )
