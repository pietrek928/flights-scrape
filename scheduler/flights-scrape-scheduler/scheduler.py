# google-chrome-stable --allow-running-insecure-content
# gunicorn -b '0.0.0.0:8090' --workers=1 --env=AIRPORTS=WAW,ALC,MAN --env=END_DATE=2025-08-01 'scheduler.scheduler:make_app()'

import json
import logging
import lzma as xz
from os import environ, makedirs, path
from uuid import uuid4, UUID

import aiofiles
from flask import Flask
from flask_cors import CORS

from . import ryanair, wizzair
from .utils import json_request


app = Flask(__name__, static_folder=None)

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


@app.route('/storage/save_result', methods=['POST'])
@json_request
async def save_result_(dataset_name, result):
    await save_result(dataset_name, result)


def make_app():
    global END_DATE

    # We always need cors here
    CORS(app, origins='*', supports_credentials=True)
    app.register_blueprint(ryanair.make_blueprint())
    app.register_blueprint(wizzair.make_blueprint())

    return app


if __name__ == '__main__':
    make_app().run(host='0.0.0.0', port=8090, debug=True)

# TODO: use many proxies, create different versions browser profiles
