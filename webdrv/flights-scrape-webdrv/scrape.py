from asyncio import create_task, run
import json
import httpx
import websockets

from .utils import sleep_rand
from .webdrv import BrowserConnection, WSTab
from .control import fetch_requests_body, get_element_center, get_next_element_center
from .ryanair import list_all_airports


async def test():
    async with httpx.AsyncClient() as client:
        conn = BrowserConnection(client, 'http://127.0.0.1:9222')
        ws_url = await conn.open_new_tab()

        async with websockets.connect(ws_url) as websocket:
            tab = WSTab(websocket)
            await tab.send_command("Network.enable")
            await tab.send_command("Page.enable")
            await tab.send_command('Page.navigate', url='https://www.wizzair.com/en-gb/booking/select-flight/WAW/CPH/2025-09-27/null/1/0/0/null')
            # await tab.send_command('Page.navigate', url='https://www.ryanair.com/pl/pl/trip/flights/select?adults=1&teens=0&children=0&infants=0&dateOut=2025-10-14&dateIn=&isConnectedFlight=false&discount=0&promoCode=&isReturn=false&originIata=WAW&destinationIata=AGP&tpAdults=1&tpTeens=0&tpChildren=0&tpInfants=0&tpStartDate=2025-10-14&tpEndDate=&tpDiscount=0&tpPromoCode=&tpOriginIata=WAW&tpDestinationIata=AGP')
            create_task(tab.process_events())

            print("Connected to Brave via WebSocket!")
            await sleep_rand(1, 2)
            async for url, content_future in fetch_requests_body(tab, 'https://be.wizzair.com'):
                content = await content_future
                print(url, content)

            # print(await get_element_center(tab, '.is-date-selected'))
            # print(await get_next_element_center(tab, '.is-date-selected'))
            # print(await list_all_airports(tab))

run(test())
