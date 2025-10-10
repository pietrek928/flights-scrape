from collections import defaultdict
from functools import partial
import json
import logging
from asyncio import create_task, shield
from typing import List, Tuple
from datetime import datetime, timedelta
import websockets

from .control import fetch_requests_body, get_element_center, get_element_text, get_next_element_center, get_response_body, left_click, move_mouse_sim, save_post_payloads, send_text
from .utils import new_id, sleep_rand
from .webdrv import WSTab
from .store import save_result
from .job import Job, load_jobs, run_jobs, save_jobs


class QueryWizzairDates(Job):
    src_code: str
    dst_code: str
    fwd_count: int


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
        date_string = date_string.strip()
        if date_string:
            parsed = datetime.strptime(date_string.strip(), "%a %d, %b")
            dates.append(parsed.replace(year=current_year-1))
            dates.append(parsed.replace(year=current_year))
            dates.append(parsed.replace(year=current_year+1))
    return sum(
        0 < (d - start_datetime).days <= days for d in dates
    )


def make_jobs(src_codes: Tuple[str, ...], dst_codes: Tuple[str, ...], fwd_count: int):
    for src_code in src_codes:
        for dst_code in dst_codes:
            if src_code != dst_code:
                yield QueryWizzairDates(
                    id=new_id(),
                    src_code=src_code,
                    dst_code=dst_code,
                    fwd_count=fwd_count
                )


def make_dates_jobs(
    src_code: str, dst_code: str, dates: Tuple[str, ...], days_after: int = 6
):
    dates = sorted(dates, reverse=True)
    while dates:
        date = dates.pop()
        date_start = datetime.strptime(date, '%Y-%m-%d')
        date_end = (date_start - timedelta(days=days_after+1)).strftime('%Y-%m-%d')
        while dates and dates[-1] <= date_end:
            dates.pop()

        yield QueryWizzairFlights(
            id=new_id(),
            src_code=src_code,
            dst_code=dst_code,
            start_date=date,
            days=days_after
        )


async def process_responses(tab: WSTab, payloads: dict, jobs: List, processed_dates: defaultdict[set]):
    async for url, request_id in fetch_requests_body(tab, 'https://be.wizzair.com/'):
        if 'Api/asset/map' in url:
            pass
            # body = await get_response_body(tab, request_id)
        elif '/Api/search/search' in url:
            body = await get_response_body(tab, request_id)
            if not body:
                logging.warning(f'Wizzair empty body for {url}')
                continue

            payload = payloads.get(request_id)
            logging.info(f'Wizzair body={len(body)} payload={len(payload or '')} url={url}')
            await save_result('wizzair', dict(
                body=json.loads(body),
                payload=payload,
                url=url,
                fetch_timestamp=datetime.now().isoformat(),
            ))
        elif '/Api/search/flightDates' in url:
            body = await get_response_body(tab, request_id)
            if not body:
                logging.warning(f'Wizzair empty body for {url}')
                continue

            src_code = None
            dst_code = None
            for part in url.split('?')[-1].split('&'):
                if part.startswith('departureStation='):
                    src_code = part.split('=')[-1]
                elif part.startswith('arrivalStation='):
                    dst_code = part.split('=')[-1]
            if src_code and dst_code:
                dates = tuple(
                    d.split('T')[0] for d in json.loads(body)['flightDates']
                )
                dates = set(dates) - processed_dates[(src_code, dst_code)]
                jobs_key = (src_code, dst_code)
                jobs.extend(make_dates_jobs(src_code, dst_code, dates))
                processed_dates[jobs_key].update(dates)
                logging.info(f'Wizzair found {len(dates)} dates for {src_code}-{dst_code}, total jobs: {len(jobs)}')


def get_job_url(job: QueryWizzairFlights):
    return (
        f'https://www.wizzair.com/en-gb/booking/select-flight/'
        f'{job.src_code}/{job.dst_code}/{job.start_date}/null/1/0/0/null'
    )

async def select_1way_dates(tab: WSTab, src_code: str, dst_code: str):
    await tab.navigate(f'https://www.wizzair.com/en-gb')
    await sleep_rand(4, 5)

    centers = await get_element_center(tab, r'[value="oneway"]')
    x, y = centers[0]
    await move_mouse_sim(tab, 0, 0, x, y)
    await sleep_rand(0.2, 0.2)
    await left_click(tab, x, y, rand_move=5)
    xp, yp = x, y

    await sleep_rand(1, 2)
    centers = await get_element_center(tab, r'[placeholder="Origin"]')
    x, y = centers[0]
    await move_mouse_sim(tab, xp, yp, x, y)
    await sleep_rand(0.5, 0.3)
    await left_click(tab, x, y)
    await send_text(tab, src_code)
    await sleep_rand(1, 2)
    await send_text(tab, '{Enter}')
    xp, yp = x, y
    
    await sleep_rand(1, 2)
    centers = await get_element_center(tab, r'[placeholder="Destination"]')
    x, y = centers[0]
    await move_mouse_sim(tab, xp, yp, x, y)
    await sleep_rand(0.5, 0.3)
    await left_click(tab, x, y)
    await send_text(tab, dst_code)
    await sleep_rand(1, 2)
    await send_text(tab, '{Enter}')
    xp, yp = x, y

    await sleep_rand(1, 2)
    centers = await get_element_center(tab, r'[placeholder="Departure"]')
    x, y = centers[0]
    await move_mouse_sim(tab, xp, yp, x, y)
    await sleep_rand(0.5, 0.3)
    await left_click(tab, x, y)


async def click_next_date(tab: WSTab):
    centers = await get_element_center(tab, r'[aria-label="Later dates"]')
    if not centers:
        return False

    x, y = centers[0]
    await move_mouse_sim(tab, 0, 0, x, y)
    await sleep_rand(0.2, 0.2)
    await left_click(tab, x, y, rand_move=5)

    return True


async def process_job(tab: WSTab, job: Job) -> Tuple[Job, ...]:
    if isinstance(job, QueryWizzairFlights):
        await tab.navigate(get_job_url(job))
        await sleep_rand(8, 6)

        all_dates = await get_element_text(tab, r'[data-test="flight-date-picker-chart"] .column:not(.is-no-flight)')
        logging.info(f'Read wizzair dates {all_dates}')
        dates_after = count_dates_after(all_dates, job.start_date, job.days)
        logging.info(f'Found {dates_after} wizzair dates')

        for _ in range(dates_after):
            centers = await get_next_element_center(
                tab,
                r'[data-test="flight-date-picker-chart"] .column.is-date-selected',
                r':not(.is-no-flight)',
                r'.date'
            )
            if not centers:
                logging.warning('No next date found')
                break

            x, y = centers[0]
            await move_mouse_sim(tab, 0, 0, x, y)
            await sleep_rand(0.5, 0.3)
            await left_click(tab, x, y)
            # await tab.highlight_square(x, y, size=30)
            print('click', x, y)
            await sleep_rand(8, 6)
    
    elif isinstance(job, QueryWizzairDates):
        await select_1way_dates(tab, job.src_code, job.dst_code)
        await sleep_rand(4, 6)
        for it in range(job.fwd_count):
            if not await click_next_date(tab):
                break
            logging.info(f'Clicked next date page {it+1}/{job.fwd_count}')
            await sleep_rand(4, 6)

    else:
        raise ValueError(f'Unknown job type: {job}')


async def make_worker(conn, jobs, processed_dates):
    ws_url = await conn.open_new_tab()
    websocket = await websockets.connect(ws_url).__aenter__()
    tab = WSTab(websocket)
    payloads = {}
    shield(create_task(save_post_payloads(tab, payloads, 'https://be.wizzair.com/')))
    shield(create_task(process_responses(tab, payloads, jobs, processed_dates)))
    shield(create_task(tab.process_events()))
    await tab.send_command("Page.enable")
    await tab.send_command("Input.enable")
    await tab.send_command("Network.enable")
    await sleep_rand(4, 6)
    logging.info('Wizzair tab opened')
    return tab


async def download_wizzair(browser_conn, airports, start_date, end_date):
    try:
        jobs, processed_dates = load_jobs('wizzair_jobs.json', Job)
        jobs = list(jobs)
    except FileNotFoundError:
        jobs = list(make_jobs(
            airports, airports, fwd_count=(end_date - start_date).days // 60 + 1
        ))
        processed_dates = defaultdict(set)
    try:
        await run_jobs(
            jobs, process_job, partial(make_worker, browser_conn, jobs, processed_dates),
            max_workers=1, max_worker_jobs=8
        )
    finally:
        save_jobs('wizzair_jobs.json', (jobs, processed_dates))
