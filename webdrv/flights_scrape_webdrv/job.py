import json
import logging
from asyncio import create_task, wait, FIRST_COMPLETED
from random import shuffle, uniform
from typing import List, Tuple
from pydantic import BaseModel

from .utils import get_all_subclasses, safe_format_json


class Job(BaseModel):
    id: str


def save_jobs(fname, jobs):
    with open(fname, 'w') as f:
        json.dump(safe_format_json(jobs), f)
        logging.info(f'Saved jobs as `{fname}`')


def _parse_jobs(obj, subclasses):
    if isinstance(obj, (list, tuple, set)):
        return tuple(_parse_jobs(o, subclasses) for o in obj)
    elif isinstance(obj, dict):
        if 'type_' in obj:
            job_type = obj.pop('type_')
            if job_type not in subclasses:
                raise ValueError(f'Unknown job type: {job_type}')
            return subclasses[job_type].model_validate(obj)
        else:
            return {k: _parse_jobs(v, subclasses) for k, v in obj.items()}
    return obj


def load_jobs(fname, base_cls):
    subclasses = get_all_subclasses(base_cls)
    with open(fname) as f:
        return _parse_jobs(json.load(f), subclasses)


async def _process_job(process_job, worker, job, worker_jobs_limit):
    worker_jobs_limit -= 1
    return worker, await process_job(worker, job), job.id, worker_jobs_limit


async def run_jobs(
    jobs: List[Job], process_job,
    make_worker, max_workers, max_worker_jobs
):
    executed_jobs = {}
    shuffle(jobs)
    working_jobs = set()
    try:
        while jobs or working_jobs:
            if working_jobs:
                free_workers = []
                done, working_jobs = await wait(
                    working_jobs, return_when=FIRST_COMPLETED, timeout=uniform(1, 2)
                )
                for job_result in done:
                    worker, new_jobs, job_id, worker_jobs_limit = await job_result
                    executed_jobs.pop(job_id, None)
                    if worker_jobs_limit > 0:
                        free_workers.append((worker, worker_jobs_limit))
                    else:
                        await worker.close()
                    if new_jobs:
                        jobs.extend(new_jobs)
                        shuffle(jobs)

                while free_workers and jobs:
                    worker, worker_jobs_limit = free_workers.pop()
                    job = jobs.pop()
                    working_jobs.add(create_task(
                        _process_job(process_job, worker, job, worker_jobs_limit)
                    ))
                    executed_jobs[job.id] = job

            while len(working_jobs) < max_workers and jobs:
                job = jobs.pop()
                working_jobs.add(create_task(
                    _process_job(process_job, await make_worker(), job, max_worker_jobs)
                ))
                executed_jobs[job.id] = job
        for worker, worker_jobs_limit in working_jobs:
            await worker.close()
    finally:
        jobs.extend(executed_jobs.values())
