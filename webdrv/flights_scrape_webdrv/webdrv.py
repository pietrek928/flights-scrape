from asyncio import Future, Queue
import json
from httpx import AsyncClient
from websockets import ConnectionClosedError


class BrowserConnection:
    def __init__(self, client: AsyncClient, base_url: str):
        self.client = client
        self.base_url = base_url

    async def get_info(self):
        response = await self.client.get(f'{self.base_url}/json/version')
        return response.json()

    async def list_targets(self):
        response = await self.client.get(f'{self.base_url}/json/list')
        return response.json()

    async def open_new_tab(self) -> str:
        response = await self.client.put(
            f"{self.base_url}/json/new"
        )
        return response.json()["webSocketDebuggerUrl"]


class WSTab:
    def __init__(self, websocket):
        self.websocket = websocket
        self.message_id = 1
        self.events = {}

    async def set_event_id(self, key):
        if key in self.events:
            raise ValueError(f'Event with id {key} already exists')
        self.events[key] = Future()

    async def wait_for_event(self, key):
        e = self.events.get(key)
        if e is None:
            raise ValueError(f'Event with id {key} does not exist')
        try:
            return await e
        finally:
            self.events.pop(key, None)

    async def start_method_queue(self, method: str):
        if method in self.events:
            raise ValueError(f'Method {method} already has a queue')
        self.events[method] = Queue()

    async def listen_method(self, method: str):
        added = False
        try:
            if method not in self.events:
                await self.start_method_queue(method)
                added = True
            while True:
                yield await self.events[method].get()
        finally:
            if added:
                self.events.pop(method, None)

    async def process_message(self, data):
        # print(data)
        if 'id' in data:
            key = data['id']
        elif 'method' in data:
            key = data['method']
        else:
            return

        exc_info = None
        value = None
        if 'result' in data:
            result = data['result']
            if 'exceptionDetails' in result:
                exc_info = result['exceptionDetails']
            elif 'result' in result:
                value = result['result']
            else:
                value = result
        elif 'params' in data:
            value = data['params']
        else:
            value = data

        evt = self.events.get(key)
        if isinstance(evt, Future):
            if exc_info is not None:
                evt.set_exception(RuntimeError(f'{key} failed: {exc_info}'))
            else:
                evt.set_result(value)
        elif isinstance(evt, Queue):
            await evt.put(value)

    async def process_events(self):
        try:
            async for message in self.websocket:
                await self.process_message(json.loads(message))
        except ConnectionClosedError:
            pass

    async def send_command(self, method, bind=False, **params):
        message_id = self.message_id
        self.message_id += 1

        if bind:
            await self.set_event_id(message_id)
        await self.websocket.send(json.dumps({
            'id': message_id,
            'method': method,
            'params': dict(params)
        }))
        return message_id

    async def navigate(self, url: str):
        return await self.send_command('Page.navigate', url=url)

    # mousePressed, mouseReleased
    async def left_click(self, x, y, event_type, click_count=1):
        return await self.send_command(
            'Input.dispatchMouseEvent',
            type=event_type,
            x=x,
            y=y,
            button='left',
            clickCount=click_count
        )

    async def cursor_move(self, x, y):
        await self.send_command(
            'Input.dispatchMouseEvent',
            type='mouseMoved',
            x=x,
            y=y
        )

    async def run_code(self, js_code, bind=False):
        return await self.send_command(
            'Runtime.evaluate', bind=bind,
            expression=js_code,
            objectGroup='console',
            includeCommandLineAPI=True,
            silent=False,
            returnByValue=True,
            generatePreview=True,
            userGesture=True,
            awaitPromise=True
        )

    async def close(self):
        await self.send_command('Page.close')

        for e in self.events.values():
            if isinstance(e, Future):
                e.cancel()
            elif isinstance(e, Queue):
                await e.shutdown()
        self.events.clear()
