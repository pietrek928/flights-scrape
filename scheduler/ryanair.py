import atexit
from datetime import datetime, timedelta
from functools import partial
from os import environ
from typing import Dict, Tuple

from flask import Blueprint
from pydantic import BaseModel

from .utils import clear_job_locks, fetch_free_job, json_request, load_jobs, new_id, save_jobs


ryanai_blueprint = Blueprint('ryanair', __name__, url_prefix='/ryanair')


JOBS: Dict = {}
JOBS_LOCKED: Dict[str, datetime] = {}
END_DATE = 'z'


class Job(BaseModel):
    id: str


class QueryDatesJob(Job):
    src_code: str
    dst_code: str


class QueryFlightsJob(Job):
    src_code: str
    dst_code: str
    date: str
    days_before: int = 2
    days_after: int = 2


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
            src_code=src_code,
            dst_code=dst_code,
            date=date_query,
            days_before=days_before,
            days_after=days_after,
        )

def init_jobs(airports):
    jobs = {}
    for a1 in airports:
        for a2 in airports:
            if a1 != a2:
                job = QueryDatesJob(
                    id=new_id(),
                    src_code=a1,
                    dst_code=a2,
                )
                jobs[job.id] = job
    return jobs


@ryanai_blueprint.route('/fetch_job', methods=['POST'])
@json_request
async def fetch_job():
    result = fetch_free_job(JOBS, JOBS_LOCKED)
    if result is not None:
        return result

    clear_job_locks(JOBS_LOCKED)
    return fetch_free_job(JOBS, JOBS_LOCKED)


@ryanai_blueprint.route('/complete_job', methods=['POST'])
@json_request
async def complete_job(job_id):
    JOBS_LOCKED.pop(job_id, None)
    JOBS.pop(job_id, None)


@ryanai_blueprint.route('/save_flight_dates', methods=['POST'])
@json_request
async def save_flight_dates(src_code: str, dst_code: str, dates: Tuple[str, ...]):
    new_jobs = list(make_dates_jobs(src_code, dst_code, (
        d for d in dates if d <= END_DATE
    )))
    JOBS.update({
        job.id: job for job in new_jobs
    })


def make_blueprint():
    fname = 'ryanair_jobs.json'
    airports = tuple(environ['AIRPORTS'].split(','))

    try:
        JOBS.update(load_jobs(fname, Job))
    except FileNotFoundError:
        JOBS.update(init_jobs(airports))

    atexit.register(partial(save_jobs, fname, JOBS))
    return ryanai_blueprint
