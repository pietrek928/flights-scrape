from base64 import b64decode
from asyncio import Task
from random import uniform
from typing import AsyncIterator, Tuple

from .utils import sleep_rand
from .webdrv import WSTab


async def left_click(tab: WSTab, x, y, rand_move=15):
    x += uniform(-rand_move, rand_move)
    y += uniform(-rand_move, rand_move)
    await tab.left_click(x, y, 'mousePressed')
    await sleep_rand(.1, .15)
    await tab.left_click(x, y, 'mouseReleased')
    await sleep_rand(.1, .15)


async def get_element_center(tab: WSTab, selector: str):
    result_key = await tab.run_code(f'''
    Array.from(
        document.querySelectorAll('{selector}')
    ).map(element => {{
        const rect = element.getBoundingClientRect();
        return [rect.left + rect.width / 2, rect.top + rect.height / 2];
    }});
    ''', bind=True)
    return await tab.wait_for_event(result_key)


async def get_next_element_center(tab: WSTab, selector: str):
    result_key = await tab.run_code('''((selector) => {
        const centers = [];
        Array.from(
            document.querySelectorAll(selector)
        ).forEach(element => {
            element = element.nextElementSibling;
            aaaa
            if (!element) {
                return;
            }
            const rect = element.getBoundingClientRect();
            centers.push([rect.left + rect.width / 2, rect.top + rect.height / 2]);
        });
        return centers;
    })'''
    f'''('{selector}')''', bind=True)
    return await tab.wait_for_event(result_key)


async def get_element_text(tab: WSTab, selector: str):
    result_key = await tab.run_code(f'''
    Array.from(
        document.querySelectorAll('{selector}')
    ).map(element => element.textContent);
    ''', bind=True)
    return await tab.wait_for_event(result_key)


async def save_post_payloads(tab: WSTab, payloads_store: dict, url_prefix: str):
    async for params in tab.listen_method('Network.requestWillBeSent'):
        request_id = params['requestId']
        request = params['request']
        url = request['url']
        if url.startswith(url_prefix) and 'postData' in request:
            payloads_store[request_id] = request['postData']


async def get_response_body(tab: WSTab, request_id: str):
    msg_id = await tab.send_command('Network.getResponseBody', bind=True, requestId=request_id)
    data = await tab.wait_for_event(msg_id)
    if 'body' in data:
        body = data['body']
        if data.get('base64Encoded'):
            body = b64decode(body).decode('utf-8')
        return body
    elif 'error' in data:
        # raise RuntimeError(f'Failed to get response body: {data["error"]}')
        print(f'Failed to get response body: {data["error"]}')


async def fetch_requests_body(tab: WSTab, url_prefix: str) -> AsyncIterator[Tuple[str, str]]:
    async for params in tab.listen_method('Network.responseReceived'):
        request_id = params['requestId']
        response = params['response']
        url = response['url']
        if url.startswith(url_prefix):
            yield url, request_id
