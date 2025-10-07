from base64 import b64decode
from random import uniform
from typing import AsyncIterator, Optional, Tuple

from .utils import sleep_rand
from .webdrv import WSTab


async def left_click(tab: WSTab, x, y, rand_move=15):
    x += uniform(-rand_move, rand_move)
    y += uniform(-rand_move, rand_move)
    await tab.left_click(x, y, 'mousePressed')
    await sleep_rand(.1, .15)
    await tab.left_click(x, y, 'mouseReleased')
    await sleep_rand(.1, .15)


async def send_text(tab: WSTab, text: str, delay: float = 0.05):
    for seq in text.split('{'):
        if '}' in seq:
            k = seq.split('}', 1)[0]
            await tab.send_key('keyDown', key=k)
            await sleep_rand(delay * 0.8, delay * 1.2)
            await tab.send_key('keyUp', key=k)
            await sleep_rand(delay * 0.8, delay * 1.2)
        for char in seq.split('}', 1)[-1]:
            await tab.send_text(char)
            await sleep_rand(delay * 0.8, delay * 1.2)


async def move_mouse_sim(tab: WSTab, x, y, xend, yend, max_move=100, a=0.2):
    while True:
        dx = xend - x
        dy = yend - y
        dist = (dx * dx + dy * dy) ** 0.5
        if dist < 10:
            break
        dx /= dist
        dy /= dist
        if dist > max_move:
            dist = max_move
        x += dx * dist * uniform(1.0-a, 1.0+a)
        y += dy * dist * uniform(1.0-a, 1.0+a)
        await tab.cursor_move(x, y)
        await sleep_rand(0.02, 0.07)


async def get_element_center(tab: WSTab, selector: str):
    result_key = await tab.run_code(f'''
    Array.from(
        document.querySelectorAll('{selector}')
    ).map(element => {{
        const rect = element.getBoundingClientRect();
        return [rect.left + rect.width / 2, rect.top + rect.height / 2];
    }});
    ''', bind=True)
    return (await tab.wait_for_event(result_key))['value']


async def get_next_element_center(
    tab: WSTab, selector: str, next_selector: str, sub_selector: Optional[str] = None
):
    result_key = await tab.run_code('''((selector, next_selector, sub_selector) => {
        const centers = [];
        Array.from(
            document.querySelectorAll(selector)
        ).forEach(element => {
            element = element.nextElementSibling;
            while (element && !element.matches(next_selector)) {
                element = element.nextElementSibling;
            }
            if (!element) {
                return;
            }
            if (sub_selector) {
                element = element.querySelector(sub_selector);
                if (!element) {
                    return;
                }
            }
            const rect = element.getBoundingClientRect();
            centers.push([rect.left + rect.width / 2, rect.top + rect.height / 2]);
        });
        return centers;
    })'''
    f'''('{selector}', '{next_selector}', '{sub_selector or ''}')''', bind=True)
    return (await tab.wait_for_event(result_key))['value']


async def get_element_text(tab: WSTab, selector: str):
    result_key = await tab.run_code(f'''
    Array.from(
        document.querySelectorAll('{selector}')
    ).map(element => element.textContent);
    ''', bind=True)
    return (await tab.wait_for_event(result_key))['value']


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
