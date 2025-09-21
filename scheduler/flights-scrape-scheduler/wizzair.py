import atexit
from datetime import UTC, datetime, timedelta
from functools import partial
from os import environ
from typing import Dict, Tuple

from flask import Blueprint
from pydantic import BaseModel

from .utils import clear_job_locks, fetch_free_job, json_request, load_jobs, new_id, save_jobs


wizzair_blueprint = Blueprint('wizzair', __name__, url_prefix='/wizzair')


JOBS: Dict = {}
JOBS_LOCKED: Dict[str, datetime] = {}
END_DATE = 'z'


class Job(BaseModel):
    id: str


class QueryJobs(Job):
    src_code: str
    dst_code: str
    start_date: str
    days: int


def make_jobs(src_codes: Tuple[str, ...], dst_codes: Tuple[str, ...], start_date: datetime, days: int, max_days: int):
    for src_code in src_codes:
        for dst_code in dst_codes:
            if src_code != dst_code:
                for i in range(0, max_days, days):
                    yield QueryJobs(
                        id=new_id(),
                        src_code=src_code,
                        dst_code=dst_code,
                        start_date=(start_date + timedelta(days=i)).strftime('%Y-%m-%d'),
                        days=min(max_days, days - i + 1),
                    )


@wizzair_blueprint.route('/fetch_job', methods=['POST'])
@json_request
async def fetch_job():
    result = fetch_free_job(JOBS, JOBS_LOCKED)
    if result is not None:
        return result

    clear_job_locks(JOBS_LOCKED)
    return fetch_free_job(JOBS, JOBS_LOCKED)


@wizzair_blueprint.route('/complete_job', methods=['POST'])
@json_request
async def complete_job(job_id):
    JOBS_LOCKED.pop(job_id, None)
    JOBS.pop(job_id, None)


def make_blueprint():
    fname = 'wizzair_jobs.json'
    airports = tuple(environ['AIRPORTS'].split(','))

    try:
        JOBS.update(load_jobs(fname, Job))
    except FileNotFoundError:
        JOBS.update({
            str(job.id): job
            for job in make_jobs(airports, airports, datetime.now(UTC).date(), 8, 60)
        })

    atexit.register(partial(save_jobs, fname, JOBS))
    return wizzair_blueprint
