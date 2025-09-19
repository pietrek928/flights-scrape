from datetime import UTC, datetime
import json
from functools import wraps
from sys import exc_info
from traceback import format_exception
from typing import Dict
from uuid import uuid4

from flask import jsonify, request
from pydantic import BaseModel


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
        r = safe_format_json(o.model_dump())
        r['type_'] = o.__class__.__name__
        return r
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


def save_jobs(fname, jobs):
    with open(fname, 'w') as f:
        json.dump(safe_format_json(jobs), f)
        print(f'Saved {len(jobs)} jobs as `{fname}`')


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
        print(f'Loaded {len(jobs)} jobs from `{fname}`')
    return jobs


def fetch_free_job(jobs, jobs_locked):
    for job_id in reversed(tuple(jobs.keys())):
        if job_id not in jobs_locked:
            job = jobs[job_id]
            jobs_locked[job_id] = datetime.now(UTC)
            return job


def clear_job_locks(jobs_locked, timeout_s = 60 * 4):
    cur_time = datetime.now(UTC)
    for job_id, lock_time in tuple(jobs_locked.items()):
        if (cur_time - lock_time).total_seconds() > timeout_s:
            jobs_locked.pop(job_id)