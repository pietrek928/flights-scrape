from asyncio import sleep
import json
import logging
from random import random
from uuid import uuid4

from pydantic import BaseModel


async def sleep_rand(base_s: float = 2., rand_s: float = 5.):
    await sleep(base_s + random() * rand_s)


def new_id():
    return str(uuid4())


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
        r = safe_format_json(o.model_dump())
        r['type_'] = o.__class__.__name__
        return r
    else:
        return o


def save_jobs(fname, jobs):
    with open(fname, 'w') as f:
        json.dump(safe_format_json(jobs), f)
        logging.info(f'Saved {len(jobs)} jobs as `{fname}`')


def get_all_subclasses(base_cls):
    all_subclasses = {
        base_cls.__name__: base_cls
    }
    for subclass in base_cls.__subclasses__():
        all_subclasses.update(get_all_subclasses(subclass))
    return all_subclasses


def load_jobs(fname, base_cls):
    subclasses = get_all_subclasses(base_cls)
    with open(fname) as f:
        jobs = {}
        for job_id, job in json.load(f).items():
            job_type = job.pop('type_')
            if job_type not in subclasses:
                raise ValueError(f'Unknown job type: {job_type}')
            jobs[job_id] = subclasses[job_type].model_validate(job)
        logging.info(f'Loaded {len(jobs)} jobs from `{fname}`')
    return jobs
