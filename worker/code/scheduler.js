const manager_url = 'http://localhost:8090'
const storage_url = `${manager_url}/storage`
const scheduler_url = `${manager_url}/scheduler`


export const save_data = async (dataset_name, data) => {
    const url = `${storage_url}/save_result`;
    const response = await fetch(url, {
        method: 'POST',
        body: JSON.stringify({
            dataset_name: dataset_name,
            result: data,
        }),
        mode: "cors",
    });
    if (response.status !== 200) {
        throw new Error(`Server responded with status ${response.status} ${response.statusText} for ${url}`);
    }
};

export const fetch_job = async () => {
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

export const complete_job = async (job_id) => {
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

export const save_flight_dates = async (src_code, dst_code, dates) => {
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
