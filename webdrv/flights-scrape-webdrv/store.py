import json
import logging
import lzma as xz
from os import environ, makedirs, path
from uuid import UUID, uuid4

import aiofiles


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
    logging.info(f'Saving result to {fname}')
    if path.isfile(fname):
        return await save_result(dataset_name, result)

    makedirs(obj_path, exist_ok=True)
    data = xz.compress(json.dumps(result).encode('utf-8'))
    async with aiofiles.open(fname, 'wb') as f:
        await f.write(data)
