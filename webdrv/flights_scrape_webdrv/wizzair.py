import json
import logging
from asyncio import create_task, shield
from typing import Tuple
from datetime import datetime, timedelta
import websockets

from .control import fetch_requests_body, get_element_center, get_element_text, get_next_element_center, get_response_body, left_click, save_post_payloads
from .utils import new_id, sleep_rand
from .webdrv import WSTab
from .store import save_result
from .job import Job


class QueryWizzairFlights(Job):
    src_code: str
    dst_code: str
    start_date: str
    days: int


def count_dates_after(wizzair_dates, start_date, days):
    start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
    current_year = start_datetime.year
    dates = []
    for date_string in wizzair_dates:
        parsed = datetime.strptime(date_string.strip(), "%a %d, %b")
        dates.append(parsed.replace(year=current_year-1))
        dates.append(parsed.replace(year=current_year))
        dates.append(parsed.replace(year=current_year+1))
    return sum(
        0 < (d - start_datetime).days <= days for d in dates
    )


def make_jobs(src_codes: Tuple[str, ...], dst_codes: Tuple[str, ...], start_date: datetime, days: int, max_days: int):
    for src_code in src_codes:
        for dst_code in dst_codes:
            if src_code != dst_code:
                for i in range(0, max_days, days):
                    yield QueryWizzairFlights(
                        id=new_id(),
                        src_code=src_code,
                        dst_code=dst_code,
                        start_date=(start_date + timedelta(days=i)).strftime('%Y-%m-%d'),
                        days=min(max_days, days - i + 1),
                    )


async def save_responses(tab: WSTab, payloads: dict):
    async for url, request_id in fetch_requests_body(tab, 'https://be.wizzair.com/'):
        if 'Api/asset/map' in url:
            pass
            # body = await get_response_body(tab, request_id)
        elif '/Api/search/search' in url:
            body = await get_response_body(tab, request_id)
            payload = payloads.get(request_id)
            logging.info(f'Wizzair body={len(body)} payload={len(payload or '')} url={url}')
            await save_result('wizzair', dict(
                body=json.loads(body),
                payload=payload,
                url=url,
                fetch_timestamp=datetime.now().isoformat(),
            ))


def get_job_url(job: QueryWizzairFlights):
    return (
        f'https://www.wizzair.com/en-gb/booking/select-flight/'
        f'{job.src_code}/{job.dst_code}/{job.start_date}/null/1/0/0/null'
    )


async def process_job(tab: WSTab, job: Job) -> Tuple[Job, ...]:
    if isinstance(job, QueryWizzairFlights):
        await tab.navigate(get_job_url(job))
        await sleep_rand(8, 6)

        all_dates = await get_element_text(tab, r'[data-test="flight-date-picker-chart"] .column:not(.is-no-flight)')
        logging.info(f'Read wizzair dates {all_dates}')
        dates_after = count_dates_after(all_dates, job.start_date, job.days)
        logging.info(f'Found {dates_after} wizzair dates')

        for _ in range(dates_after):
            centers = await get_next_element_center(tab, r'[data-test="flight-date-picker-chart"] .column.is-date-selected', r'.date')
            x, y = centers[0]
            await left_click(tab, x, y)
            print('click', x, y)
            await sleep_rand(8, 6)

    else:
        raise ValueError(f'Unknown job type: {job}')


async def make_worker(conn):
    ws_url = await conn.open_new_tab()
    websocket = await websockets.connect(ws_url).__aenter__()
    tab = WSTab(websocket)
    payloads = {}
    shield(create_task(save_post_payloads(tab, payloads, 'https://be.wizzair.com/')))
    shield(create_task(save_responses(tab, payloads)))
    shield(create_task(tab.process_events()))
    await tab.send_command("Page.enable")
    await tab.send_command("Input.enable")
    await tab.send_command("Network.enable")
    await sleep_rand(4, 6)
    logging.info('Wizzair tab opened')
    return tab
