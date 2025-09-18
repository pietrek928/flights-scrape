const api_version = '27.16.0';


const query_available_dates = async (src_code, dst_code, date_start, date_end) => {
    const url = `https://be.wizzair.com/${api_version}/Api/search/flightDates`
            + `?departureStation=${src_code}&arrivalStation=${dst_code}`
            + `&from=${date_start}&to=${date_end}`

    const response = await fetch(url, {
        method: 'GET',
        // headers: common_headers,
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


const search_flight_details = async (src_code, dst_code, depart_date, opts) => {
    const url = `https://be.wizzair.com/${api_version}/Api/search/search`;
    const payload = `{"isFlightChange":false,"flightList":[{`
        + `"departureStation":"${src_code}","arrivalStation":"${dst_code}","departureDate":"${depart_date}T00:00:00"}`
        + `],"adultCount":${opts?.adult ?? 1},"childCount":${opts?.child ?? 0},"infantCount":${opts?.infant ?? 0}`
        + `},"wdc":true}`;

    const response = await fetch(url, {
        method: 'POST',
        // headers: common_headers,
        headers: {
            'x-kpsdk-cd': '{"workTime":1751151971445,"id":"5550984dbb9920521accf1c4c1bedd60","answers":[5,1],"duration":31.7,"d":1167,"st":1751147777549,"rst":1751147778716}',
            'x-kpsdk-ct': '0LumqdV2A02p6MNpp0N6vb85syngcgaGRuc53OC9B7ez51a4lL8Vjuwh0IfDftuG65lsYpevUhjhxdHj0ZDVUskVUbSPFxpfX2w1rqcLrPcE8nTlvAwjwx5pf1Ib0tEP7sfnhQ1uGPiuvodoRxNoX1qagzZ5rtHHZDbH5XfF',
            'x-kpsdk-v': 'j-1.1.0',
            'x-requestverificationtoken': '65bbc6cdb2264e9ea76e2f020719a5ca'
        },
        body: payload,
    });
    if (response.status !== 200) {
        throw new Error(`Server responded with status ${response.status} ${response.statusText}}`);
    }
    return {
        flights: await response.json(),
        src_code: src_code,
        dst_code: dst_code,
        depart_date: depart_date,
        fetch_date: new Date().toISOString(),
    };
};


console.log('YEEEEAH!!!!! Worker started xD');
setTimeout(async () => {
    // await worker_process();
    console.log(await query_available_dates('WAW', 'MAN', '2025-06-29', '2025-07-30'));
    console.log(await search_flight_details('WAW', 'MAN', '2025-07-10', {}));
}, 5000);
