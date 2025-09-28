import logging
from functools import partial
from datetime import datetime, timedelta
from typing import Tuple, Optional
import websockets

from .utils import new_id, sleep_rand
from .webdrv import WSTab
from .store import save_result
from .job import Job, load_jobs, run_jobs


RYANAIR_API_URL = 'https://www.ryanair.com/api'


class QueryDatesJob(Job):
    src_code: str
    dst_code: str
    start_date: str
    end_date: str


class QueryFlightsJob(Job):
    src_code: str
    dst_code: str
    date: str
    days_before: int = 2
    days_after: int = 2


def make_dates_jobs(
    src_code: str, dst_code: str, dates: Tuple[str, ...],
    days_before: int = 2, days_after: int = 2
):
    dates = sorted(dates)
    while dates:
        date = dates.pop()
        date_parsed = datetime.strptime(date, '%Y-%m-%d')
        date_query = (date_parsed - timedelta(days=days_before)).strftime('%Y-%m-%d')
        date_start = (date_parsed - timedelta(days=days_before+days_after+1)).strftime('%Y-%m-%d')
        while dates and dates[-1] >= date_start:
            dates.pop()

        yield QueryFlightsJob(
            id=new_id(),
            src_code=src_code,
            dst_code=dst_code,
            date=date_query,
            days_before=days_before,
            days_after=days_after,
        )


def init_jobs(airports, start_date, end_date):
    for a1 in airports:
        for a2 in airports:
            if a1 != a2:
                yield QueryDatesJob(
                    id=new_id(),
                    src_code=a1,
                    dst_code=a2,
                    start_date=start_date,
                    end_date=end_date,
                )


RYANAIR_HEADERS = {
    'Client': 'desktop',
    'Client-Version': '3.153.0',
}


async def make_ryanair_request(tab: WSTab, url: str):
    print(f'Ryanair: {url}')
    msg_id = await tab.run_code('''(async (url, common_headers) => {
        const response = await fetch(url, {
            method: 'GET',
            headers: common_headers,
        });
        if (response.status !== 200) {
            throw new Error(`Server responded with status ${response.status}`);
        }
        return {
            result: await response.json(),
            fetch_date: new Date().toISOString(),
        };
    })'''
    f'''('{url}', {RYANAIR_HEADERS})''', bind=True
    )
    return await tab.wait_for_event(msg_id)


async def list_all_airports(tab: WSTab):
    return await make_ryanair_request(tab, f'{RYANAIR_API_URL}/views/locate/5/airports/en/active')


async def find_dest_airports(tab: WSTab, src_code: str):
    return await make_ryanair_request(tab, f'{RYANAIR_API_URL}/views/locate/searchWidget/routes/en/airport/{src_code}')


async def query_available_dates(tab: WSTab, src_code: str, dst_code: str):
    return await make_ryanair_request(tab, f'{RYANAIR_API_URL}/farfnd/3/oneWayFares/{src_code}/{dst_code}/availabilities')


async def query_flights_details(
    tab: WSTab, src_code: str, dst_code: str,
    date: datetime, days_before=2, days_after=2,
    adult=1, teen=0, child=0, infant=0
):
    date_str = date.strftime('%Y-%m-%d')
    return await make_ryanair_request(tab,
        f'{RYANAIR_API_URL}/booking/v4/en-gb/availability'
        f'?ADT={adult}&TEEN={teen}&CHD={child}&INF={infant}'
        f'&Origin={src_code}&Destination={dst_code}&promoCode=&IncludeConnectingFlights=false'
        f'&DateOut={date_str}&DateIn='
        f'&FlexDaysBeforeOut={days_before}&FlexDaysOut={days_after}'
        f'&FlexDaysBeforeIn={days_before}&FlexDaysIn={days_after}'
        f'&RoundTrip=false&IncludePrimeFares=false&ToUs=AGREED'
    )


async def make_worker(conn):
    ws_url = await conn.open_new_tab()
    websocket = await websockets.connect(ws_url).__aenter__()
    tab = WSTab(websocket)
    await tab.send_command("Page.enable")
    await tab.send_command('Page.navigate', url='https://www.ryanair.com/pl/pl/trip/flights/select?adults=1&teens=0&children=0&infants=0&dateOut=2025-10-14&dateIn=&isConnectedFlight=false&discount=0&promoCode=&isReturn=false&originIata=WAW&destinationIata=AGP&tpAdults=1&tpTeens=0&tpChildren=0&tpInfants=0&tpStartDate=2025-10-14&tpEndDate=&tpDiscount=0&tpPromoCode=&tpOriginIata=WAW&tpDestinationIata=AGP')
    await sleep_rand(4, 6)
    return tab


async def process_job(tab: WSTab, job: Job) -> Optional[Tuple[Job, ...]]:
    print('Processing job', job)
    if isinstance(job, QueryDatesJob):
        dates_data = await query_available_dates(tab, job.src_code, job.dst_code)
        logging.info('Available dates:', dates_data)
        dates = tuple(
            d for d in dates_data['dates'] if job.start_date <= d <= job.end_date
        )
        return tuple(make_dates_jobs(job.src_code, job.dst_code, dates))
    elif isinstance(job, QueryFlightsJob):
        date_parsed = datetime.strptime(job.date, '%Y-%m-%d')
        details_data = await query_flights_details(
            tab, job.src_code, job.dst_code, date_parsed,
            days_before=job.days_before, days_after=job.days_after
        )
        logging.info('Flight details:', details_data)
        await save_result('ryanair', details_data | {
            'type': 'details',
            'src_code': job.src_code,
            'dst_code': job.dst_code,
            'date': job.date
        })
    else:
        raise ValueError(f'Unknown job type: {job}')


async def download_ryanair(browser_conn, airports, start_date, end_date):
    try:
        jobs = load_jobs('ryanair_jobs.json', Job)
    except FileNotFoundError:
        jobs = tuple(init_jobs(airports, start_date, end_date))
    await run_jobs(
        jobs, process_job, partial(make_worker, browser_conn),
        max_workers=1, max_worker_jobs=1,
        save_jobs_fname='ryanair_jobs.json'
    )
