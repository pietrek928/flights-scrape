from datetime import datetime, timedelta
from typing import Tuple
from pydantic import BaseModel

from .utils import new_id
from .webdrv import WSTab
from .store import save_result


RYANAIR_API_URL = 'https://www.ryanair.com/api'


class Job(BaseModel):
    id: str


class QueryDatesJob(Job):
    src_code: str
    dst_code: str


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


def init_jobs(airports):
    jobs = {}
    for a1 in airports:
        for a2 in airports:
            if a1 != a2:
                job = QueryDatesJob(
                    id=new_id(),
                    src_code=a1,
                    dst_code=a2,
                )
                jobs[job.id] = job
    return jobs


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


# const process_fetch_dates = async (src_code, dst_code) => {
#     const dates = await query_available_dates(src_code, dst_code);
#     await save_flight_dates(src_code, dst_code, dates.dates);
# };

# const process_fetch_details = async (src_code, dst_code, date) => {
#     const details = await query_flights_details(src_code, dst_code, date);
#     await save_data('ryanair', details);
# };

# const process_job = async () => {
#     const job_data = await fetch_job('ryanair');
#     console.log(job_data);
#     if (!job_data) {
#         console.log('No jobs available');
#         return;
#     }
#     console.log('Fetched job', job_data);

#     switch(job_data.type_) {
#         case 'QueryDatesJob':
#             await process_fetch_dates(job_data.src_code, job_data.dst_code);
#             break;
#         case 'QueryFlightsJob':
#             await process_fetch_details(job_data.src_code, job_data.dst_code, job_data.date);
#             break;
#         default:
#             throw new Error(`Unknown job type ${job_data.type}`);
#     }

#     await complete_job('ryanair', job_data.id);
# };

async def process_job(tab: WSTab, job: Job):
    print('Processing job', job)
    if isinstance(job, QueryDatesJob):
        dates_data = await query_available_dates(tab, job.src_code, job.dst_code)
        print('Available dates:', dates_data)
        new_jobs = list(make_dates_jobs(job.src_code, job.dst_code, (
            d for d in dates_data['dates'] if d <= END_DATE
        )))
        JOBS.update({
            job.id: job for job in new_jobs
        })
        # return dates_data | {
        #     'type': 'dates',
        #     'src_code': job.src_code,
        #     'dst_code': job.dst_code
        # }
    elif isinstance(job, QueryFlightsJob):
        date_parsed = datetime.strptime(job.date, '%Y-%m-%d')
        details_data = await query_flights_details(
            tab, job.src_code, job.dst_code, date_parsed,
            days_before=job.days_before, days_after=job.days_after
        )
        print('Flight details:', details_data)
        await save_result('ryanair', details_data | {
            'type': 'details',
            'src_code': job.src_code,
            'dst_code': job.dst_code,
            'date': job.date
        })
    else:
        raise ValueError(f'Unknown job type: {job}')