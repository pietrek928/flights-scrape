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
    elif isinstance(o, (list, tuple, set)):
        return tuple(
            safe_format_json(v) for v in o
        )
    elif isinstance(o, BaseModel):
        r = safe_format_json(o.model_dump())
        r['type_'] = o.__class__.__name__
        return r
    else:
        return o


def get_all_subclasses(base_cls):
    all_subclasses = {
        base_cls.__name__: base_cls
    }
    for subclass in base_cls.__subclasses__():
        all_subclasses.update(get_all_subclasses(subclass))
    return all_subclasses
