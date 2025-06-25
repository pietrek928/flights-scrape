# google-chrome-stable --allow-running-insecure-content
# gunicorn -b '0.0.0.0:8090' --workers=1 --env=AIRPORTS=WAW,ALC,MAN --env=END_DATE=2025-08-01 'scheduler.scheduler:make_app()'

import atexit
import json
import lzma as xz
from datetime import UTC, datetime, timedelta
from functools import wraps
from os import environ, makedirs, path
from sys import exc_info
from traceback import format_exception
from typing import Dict, Tuple
from uuid import uuid4, UUID

import aiofiles
from flask import Flask, jsonify, request
from flask_cors import CORS
from pydantic import BaseModel


class Job(BaseModel):
    id: str
    type_: str


class QueryDatesJob(Job):
    src_code: str
    dst_code: str


class QueryFlightsJob(Job):
    src_code: str
    dst_code: str
    date: str
    days_before: int = 2
    days_after: int = 2


app = Flask(__name__, static_folder=None)


def _parse_args(args: Dict[str, str]):
    parsed = {}
    for k, v in args.items():
        if v[0] in ('[', '{') and v[-1] in (']', '}'):
            try:
                parsed[k] = json.loads(v)
            except Exception as e:
                raise ValueError(f'Failed to parse JSON for {k}: {e}') from e
        else:
            parsed[k] = v
    return parsed


def safe_format_json(o):
    if isinstance(o, dict):
        return {
            k: safe_format_json(v) for k, v in o.items()
        }
    elif isinstance(o, (list, tuple)):
        return tuple(
            safe_format_json(v) for v in o
        )
    elif isinstance(o, BaseModel):
        return safe_format_json(o.model_dump())
    else:
        return o


def json_request(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            if request.method == 'POST':
                if request.data:
                    kwargs.update(
                        json.loads(request.data)
                    )
            kwargs.update(
                _parse_args(request.args)
            )
            return jsonify(safe_format_json(
                await func(*args, **kwargs)
            )), 200
        except ValueError as e:
            return jsonify(safe_format_json(dict(
                error=str(e),
            ))), 400
        except Exception as e:
            return jsonify(safe_format_json(dict(
                stack=format_exception(*exc_info()),
                error=str(e),
                type=type(e).__name__,
            ))), 500

    return wrapper


def new_id():
    return str(uuid4())


DATASET_PATH = environ.get('DATASET_PATH', 'datasets')


def make_object_path(dataset_name, obj_id: UUID):
    s = str(obj_id).replace('-', '')
    d1 = s[:2]
    d2 = s[2:4]
    d3 = s[4:6]
    d4 = s[6:8]
    d5 = s[8:10]
    return f'{DATASET_PATH}/{dataset_name}/{d1}/{d2}/{d3}/{d4}/{d5}'


async def save_result(dataset_name, result):
    obj_id = uuid4()
    obj_path = make_object_path(dataset_name, obj_id)
    fname = f'{obj_path}/{obj_id}.json.xz'
    print(f'Saving result to {fname}')
    if path.isfile(fname):
        return await save_result(dataset_name, result)

    makedirs(obj_path, exist_ok=True)
    data = xz.compress(json.dumps(result).encode('utf-8'))
    async with aiofiles.open(fname, 'wb') as f:
        await f.write(data)


def make_dates_jobs(
    src_code: str, dst_code: str, dates: Tuple[str, ...],
    days_before: int = 2, days_after: int = 2
):
    dates = sorted(dates)
    while dates:
        date = dates.pop()
        date_parsed = datetime.strptime(date, '%Y-%m-%d')
        date_query = (date_parsed - timedelta(days=days_before)).strftime('%Y-%m-%d')
        date_start = (date_parsed - timedelta(days=days_before+days_after+1)).strftime('%Y-%m-%d')
        while dates and dates[-1] >= date_start:
            dates.pop()

        yield QueryFlightsJob(
            id=new_id(),
            type_='QueryFlightsJob',
            src_code=src_code,
            dst_code=dst_code,
            date=date_query,
            days_before=days_before,
            days_after=days_after,
        )
            

@app.route('/storage/save_result', methods=['POST'])
@json_request
async def save_result_(dataset_name, result):
    await save_result(dataset_name, result)


JOBS: Dict[str, Job] = {}
JOBS_LOCKED: Dict[str, datetime] = {}
END_DATE = 'z'


def load_jobs(airports):
    global JOBS
    try:
        with open('saved_jobs.json') as f:
            JOBS = {}
            for job_id, job in json.load(f).items():
                match job['type_']:
                    case 'QueryDatesJob':
                        JOBS[job_id] = QueryDatesJob.model_validate(job)
                    case 'QueryFlightsJob':
                        JOBS[job_id] = QueryFlightsJob.model_validate(job)
                    case _:
                        raise ValueError(f'Unknown job type: {job["type_"]}')
            print(f'Loaded {len(JOBS)} jobs')
    except FileNotFoundError:
        for a1 in airports:
            for a2 in airports:
                if a1 != a2:
                    job = QueryDatesJob(
                        id=new_id(),
                        type_='QueryDatesJob',
                        src_code=a1,
                        dst_code=a2,
                    )
                    JOBS[job.id] = job
        print(f'Initialized {len(JOBS)} jobs')


def save_jobs():
    with open('saved_jobs.json', 'w') as f:
        json.dump(safe_format_json(JOBS), f)
        print(f'Saved {len(JOBS)} jobs')


def fetch_free_job():
    for job_id in reversed(tuple(JOBS.keys())):
        if job_id not in JOBS_LOCKED:
            job = JOBS[job_id]
            JOBS_LOCKED[job_id] = datetime.now(UTC)
            return job


def clear_job_locks():
    cur_time = datetime.now(UTC)
    for job_id, lock_time in tuple(JOBS_LOCKED.items()):
        if (cur_time - lock_time).total_seconds() > 60 * 4:
            JOBS_LOCKED.pop(job_id)


@app.route('/scheduler/fetch_job', methods=['POST'])
@json_request
async def fetch_job():
    result = fetch_free_job()
    if result is not None:
        return result

    clear_job_locks()
    return fetch_free_job()


@app.route('/scheduler/complete_job', methods=['POST'])
@json_request
async def complete_job(job_id):
    JOBS_LOCKED.pop(job_id, None)
    JOBS.pop(job_id, None)


@app.route('/scheduler/save_flight_dates', methods=['POST'])
@json_request
async def save_flight_dates(src_code: str, dst_code: str, dates: Tuple[str, ...]):
    new_jobs = list(make_dates_jobs(src_code, dst_code, (
        d for d in dates if d <= END_DATE
    )))
    JOBS.update({
        job.id: job for job in new_jobs
    })


def make_app():
    global END_DATE

    # We always need cors here
    CORS(app, origins='*', supports_credentials=True)
    load_jobs(environ['AIRPORTS'].split(','))
    END_DATE = environ.get('END_DATE') or END_DATE
    atexit.register(save_jobs)
    return app


if __name__ == '__main__':
    make_app().run(host='0.0.0.0', port=8090, debug=True)

# TODO: use many proxies, create different versions browser profiles
