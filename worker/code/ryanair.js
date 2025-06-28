const init_iframe = () => {
    const iframe = document.createElement('iframe');
    iframe.style.display = 'none';
    document.body.appendChild(iframe);
    return iframe;
}

const execute_in_iframe = (iframe, func) => {
    const iframe_window = iframe.contentWindow;
    const iframe_document = iframe_window.document;
    const iframe_div = iframe_document.createElement('div');
    iframe_div.addEventListener('click', func);
    iframe_div.click();
};

const common_headers = {
    'Client': 'desktop',
    'Client-Version': '3.153.0',
};

const list_all_airports = async () => {
    const url = 'https://www.ryanair.com/api/views/locate/5/airports/en/active';

    const response = await fetch(url, {
        method: 'GET',
        headers: common_headers,
    });
    if (response.status !== 200) {
        throw new Error(`Server responded with status ${response.status} ${response.statusText}}`);
    }
    return {
        airports: await response.json(),
        fetch_date: new Date().toISOString(),
    };
};

const find_dest_airpoits = async (src_code) => {
    const url = `https://www.ryanair.com/api/views/locate/searchWidget/routes/en/airport/${src_code}`;

    const response = await fetch(url, {
        method: 'GET',
        headers: common_headers,
    });
    if (response.status !== 200) {
        throw new Error(`Server responded with status ${response.status} ${response.statusText}}`);
    }
    return {
        airports: await response.json(),
        src_code: src_code,
        fetch_date: new Date().toISOString(),
    };
};

const query_available_dates = async (src_code, dst_code) => {
    const url = `https://www.ryanair.com/api/farfnd/3/oneWayFares/${src_code}/${dst_code}/availabilities`

    const response = await fetch(url, {
        method: 'GET',
        headers: common_headers,
    });
    if (response.status !== 200) {
        throw new Error(`Server responded with status ${response.status} ${response.statusText}}`);
    }
    return {
        dates: await response.json(),
        src_code: src_code,
        dst_code: dst_code,
        fetch_date: new Date().toISOString(),
    };
};

const query_flights_details = async (
    src_code, dst_code, date, opts
) => {
    const url = `https://www.ryanair.com/api/booking/v4/en-gb/availability`
        + `?ADT=${opts?.adult ?? 1}&TEEN=${opts?.teen ?? 0}&CHD=${opts?.child ?? 0}&INF=${opts?.infant ?? 0}`
        + `&Origin=${src_code}&Destination=${dst_code}&promoCode=&IncludeConnectingFlights=false`
        + `&DateOut=${date}&DateIn=`
        + `&FlexDaysBeforeOut=${opts?.days_before ?? 2}&FlexDaysOut=${opts?.days_after ?? 2}`
        + `&FlexDaysBeforeIn=${opts?.days_before ?? 2}&FlexDaysIn=${opts?.days_after ?? 2}`
        + `&RoundTrip=false&IncludePrimeFares=false&ToUs=AGREED`;

    const response = await fetch(url, {
        method: 'GET',
        headers: common_headers
    });
    if (response.status !== 200) {
        throw new Error(`Server responded with status ${response.status} ${response.statusText}}`);
    }
    return {
        booking: await response.json(),
        src_code: src_code,
        dst_code: dst_code,
        date: date,
        fetch_date: new Date().toISOString(),
    };
};

const manager_url = 'http://localhost:8090'
const storage_url = `${manager_url}/storage`
const scheduler_url = `${manager_url}/scheduler`

const save_data = async (data) => {
    const url = `${storage_url}/save_result`;
    const response = await fetch(url, {
        method: 'POST',
        body: JSON.stringify({
            dataset_name: 'ryanair',
            result: data,
        }),
        mode: "cors",
    });
    if (response.status !== 200) {
        throw new Error(`Server responded with status ${response.status} ${response.statusText} for ${url}`);
    }
};

const fetch_job = async () => {
    const url = `${scheduler_url}/fetch_job`;
    const response = await fetch(url, {
        method: 'POST',
        body: '',
        mode: "cors",
    });
    if (response.status !== 200) {
        throw new Error(`Server responded with status ${response.status} ${response.statusText} for ${url}`);
    }
    return await response.json();
};

const complete_job = async (job_id) => {
    const url = `${scheduler_url}/complete_job`;
    const response = await fetch(url, {
        method: 'POST',
        body: JSON.stringify({
            job_id: job_id,
        }),
        mode: "cors",
    });
    if (response.status !== 200) {
        throw new Error(`Server responded with status ${response.status} ${response.statusText} for ${url}`);
    }
};

const save_flight_dates = async (src_code, dst_code, dates) => {
    const url = `${scheduler_url}/save_flight_dates`;
    const response = await fetch(url, {
        method: 'POST',
        body: JSON.stringify({
            src_code: src_code,
            dst_code: dst_code,
            dates: dates,
        }),
        mode: "cors",
    });
    if (response.status !== 200) {
        throw new Error(`Server responded with status ${response.status} ${response.statusText} for ${url}`);
    }
};

const sleep = (base_s=2000, rand_s=5000) => new Promise((resolve) => setTimeout(resolve, base_s + Math.random() * rand_s))

const process_fetch_dates = async (src_code, dst_code) => {
    const dates = await query_available_dates(src_code, dst_code);
    await save_flight_dates(src_code, dst_code, dates.dates);
};

const process_fetch_details = async (src_code, dst_code, date) => {
    const details = await query_flights_details(src_code, dst_code, date);
    await save_data(details);
};

const process_job = async () => {
    const job_data = await fetch_job();
    console.log(job_data);
    if (!job_data) {
        console.log('No jobs available');
        return;
    }
    console.log('Fetched job', job_data);

    switch(job_data.type_) {
        case 'QueryDatesJob':
            await process_fetch_dates(job_data.src_code, job_data.dst_code);
            break;
        case 'QueryFlightsJob':
            await process_fetch_details(job_data.src_code, job_data.dst_code, job_data.date);
            break;
        default:
            throw new Error(`Unknown job type ${job_data.type}`);
    }

    await complete_job(job_data.id);
};

const worker_process = async () => {
    let allow_errors = 8;
    while (allow_errors > 0) {
        try {
            await process_job();
        } catch (e) {
            console.error('Job execution error', e);
            allow_errors--;
        }
        await sleep();
        await sleep();
    }
    window.close();
};

console.log('YEEEEAH!!!!! Worker started xD');
setTimeout(async () => {
    await worker_process();
    // console.log(await query_available_dates('WAW', 'MAN'));
    // console.log(await query_flights_details('WAW', 'MAN', '2025-07-10', { days_before: 2, days_after: 2 }));
}, 5000);

// TODO: simulate user behaviour
