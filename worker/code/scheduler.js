const manager_url = 'http://localhost:8090'


export const save_data = async (dataset_name, data) => {
    const url = `${storage_url}/storage/save_result`;
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


export const fetch_job = async (storage_name) => {
    const url = `${manager_url}/${storage_name}/fetch_job`;
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


export const complete_job = async (storage_name, job_id) => {
    const url = `${manager_url}/${storage_name}/complete_job`;
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


export const save_ryanair_flight_dates = async (src_code, dst_code, dates) => {
    const url = `${manager_url}/ryanair/save_flight_dates`;
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
