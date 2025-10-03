from asyncio import create_task, run, gather
from click import command, option
from datetime import datetime, timedelta
import logging
import httpx
import websockets

from .utils import sleep_rand
from .webdrv import BrowserConnection, WSTab
from .control import fetch_requests_body, get_element_center, get_next_element_center
from .ryanair import download_ryanair
from .wizzair import QueryWizzairFlights, download_wizzair, process_job


async def test():
    async with httpx.AsyncClient() as client:
        conn = BrowserConnection(client, 'http://127.0.0.1:9222')
        ws_url = await conn.open_new_tab()

        async with websockets.connect(ws_url) as websocket:
            tab = WSTab(websocket)
            # await tab.send_command("Network.enable")
            # await tab.send_command("Input.enable")
            await tab.send_command("Page.enable")
            # await tab.send_command("DOM.enable")
            # await tab.send_command("Overlay.enable")
            # await tab.send_command('Page.navigate', url='https://www.wizzair.com/en-gb/booking/select-flight/WAW/CPH/2025-09-27/null/1/0/0/null')
            # await tab.send_command('Page.navigate', url='https://www.ryanair.com/pl/pl/trip/flights/select?adults=1&teens=0&children=0&infants=0&dateOut=2025-10-14&dateIn=&isConnectedFlight=false&discount=0&promoCode=&isReturn=false&originIata=WAW&destinationIata=AGP&tpAdults=1&tpTeens=0&tpChildren=0&tpInfants=0&tpStartDate=2025-10-14&tpEndDate=&tpDiscount=0&tpPromoCode=&tpOriginIata=WAW&tpDestinationIata=AGP')
            create_task(tab.process_events())

            print("Connected to Brave via WebSocket!")
            await sleep_rand(4, 3)
            await process_job(tab, QueryWizzairFlights(
                id='1',
                src_code='WAW',
                dst_code='DBV',
                start_date='2026-07-18',
                days=6
            ))
            # async for url, content_future in fetch_requests_body(tab, 'https://be.wizzair.com'):
            #     content = await content_future
            #     print(url, content)
            await tab.close()

            # print(await get_element_center(tab, '.is-date-selected'))
            # print(await get_next_element_center(tab, '.is-date-selected'))
            # print(await get_next_element_center(tab, '.column:not(.is-no-flight)'))
            # print(await list_all_airports(tab))


def parse_list(v: str):
    return tuple(sorted(set(s.strip() for s in v.split(','))))


async def scrape_(browser_url, providers, airports, start_date, end_date):
    providers = parse_list(providers)
    airports = parse_list(airports)
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')

    logging.basicConfig(level=logging.INFO)
    logging.info(f'Providers: {providers}')
    logging.info(f'Airports: {airports}')

    async with httpx.AsyncClient() as client:
        conn = BrowserConnection(client, browser_url)
        tasks = []
        if 'ryanair' in providers:
            tasks.append(create_task(download_ryanair(
                conn, airports, start_date, end_date
            )))
        if 'wizzair' in providers:
            tasks.append(create_task(download_wizzair(
                conn, airports, start_date, end_date
            )))
        if not tasks:
            raise ValueError(f'No valid providers selected: {providers}')
        await gather(*tasks)


@command()
@option('--browser-url', type=str, default='http://127.0.0.1:9222')
@option('--providers', type=str, default='ryanair,wizzair')
@option('--airports', type=str, default='WAW,ALC,MAN')
@option('--start-date', type=str, default=datetime.now().strftime('%Y-%m-%d'))
@option('--end-date', type=str, default=(datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'))
def scrape(browser_url, providers, airports, start_date, end_date):
    return run(scrape_(browser_url, providers, airports, start_date, end_date))


# run(test())
# if __name__ == '__main__':
#     logging.basicConfig(level=logging.INFO)
#     run(test())
