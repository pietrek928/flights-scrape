from typing import Tuple
from datetime import datetime, timedelta

from .utils import new_id
from .webdrv import WSTab
from .job import Job


class QueryJobs(Job):
    src_code: str
    dst_code: str
    start_date: str
    days: int


def get_job_url(job: QueryJobs, days: int):
    from datetime import datetime, timedelta

    date = datetime.strptime(job.start_date, '%Y-%m-%d')
    date += timedelta(days=days)
    date_string = date.strftime('%Y-%m-%d')
    return (
        f'https://www.wizzair.com/en-gb/booking/select-flight/'
        f'{job.src_code}/{job.dst_code}/{date_string}/null/1/0/0/null'
    )


def make_jobs(src_codes: Tuple[str, ...], dst_codes: Tuple[str, ...], start_date: datetime, days: int, max_days: int):
    for src_code in src_codes:
        for dst_code in dst_codes:
            if src_code != dst_code:
                for i in range(0, max_days, days):
                    yield QueryJobs(
                        id=new_id(),
                        src_code=src_code,
                        dst_code=dst_code,
                        start_date=(start_date + timedelta(days=i)).strftime('%Y-%m-%d'),
                        days=min(max_days, days - i + 1),
                    )
