import { sleep } from './utils.js';
import { save_data } from './scheduler.js'
import { attachDebugger, sendDebuggerCommand } from './debug.js'
import { goTo, sendLeftClick } from './input.js'



const connectionsUrl = 'Api/asset/map';
const datesUrl = 'Api/search/flightDates';
const detailsUrl = 'Api/search/search';


const listenWizzairNetworkEvents = () => {
    let postPayloads = {};
    return chrome.debugger.onEvent.addListener((source, method, params) => {
        handleWizzairNetworkEvent(source, method, params, postPayloads);
    });
};

const handleWizzairNetworkEvent = (source, method, params, postPayloads) => {
    const requestId = params.requestId;
    const url = params.response?.url || params.request?.url || '';
    if (url.includes(connectionsUrl) || url.includes(datesUrl) || url.includes(detailsUrl)) {
        console.log(method, url);
        if (method === "Network.requestWillBeSent") {
            const request = params.request;

            if (request.method === "POST" && request.postData) {
                postPayloads[requestId] = request.postData;
                console.log(`Payload captured for request ID ${requestId}: ${request.postData}`);
            }
        }

        // Check if the event is a network response
        if (method === "Network.responseReceived") {
            console.log(`Response received: '${url}' ${requestId}`);
            // Get the response body
            chrome.debugger.sendCommand(source, "Network.getResponseBody", { requestId: requestId }, (response) => {
                if (response && response.body) {
                    try {
                        const body = JSON.parse(response.body);
                        body.url = url;
                        if (postPayloads[requestId]) {
                            const payload = JSON.parse(postPayloads[requestId]);
                            delete postPayloads[requestId];
                            body.payload = payload;
                        }
                        // setTimeout(async () => await save_data('wizzair', body), 0);
                        console.log(url, body);
                    } catch (e) {
                        console.error("Error decoding response body:", e);
                    }
                }
            });
        }
    }
}

const waitForLoad = (newTabId) => {
    return new Promise((resolve) => {
        const listener = (tabId, changeInfo, tab) => {
            if (tabId === newTabId && changeInfo.status === 'complete') {
                chrome.tabs.onUpdated.removeListener(listener);
                resolve();
            }
        };
        chrome.tabs.onUpdated.addListener(listener);
    });
};

const openTab = async (url) => {
    const newTab = await chrome.tabs.create({ url: url });
    await waitForLoad(newTab.id);
    return newTab.id;
};

const runFunctionInTab = async (tabId, func, ...args) => {
    const [result] = await chrome.scripting.executeScript({
        target: { tabId: tabId },
        func: func,
        args: args
    });
    return result.result;
}

const getElementCenter = async (tabId, cssSelector) => {
    return await runFunctionInTab(tabId, (selector) => {
        const elements = document.querySelectorAll(selector);
        return Array.from(elements).map(element => {
            const rect = element.getBoundingClientRect();
            return [rect.left + rect.width / 2, rect.top + rect.height / 2];
        });
    }, cssSelector);
};

const getNextElementCenter = async (tabId, cssSelector) => {
    return await runFunctionInTab(tabId, (selector) => {
        let element = document.querySelector(selector);
        if (!element) {
            return null;
        }
        element = element.nextElementSibling;
        if (!element) {
            return null;
        }
        const rect = element.getBoundingClientRect()
        return [rect.left + rect.width / 2, rect.top + rect.height / 2];
    }, cssSelector);
};

const getElementText = async (tabId, cssSelector) => {
    return await runFunctionInTab(tabId, (selector) => {
        return Array.from(document.querySelectorAll(selector)).map(element => element.textContent);
    }, cssSelector);
};

const getAvailableDates = async (tabId) => {
    return await getElementText(tabId, '.column > .date');
};

const getJobUrl = (job, days) => {
    const date = new Date(job.start_date);
    date.setDate(date.getDate() + days);
    const dateString = date.toISOString().split('T')[0];
    return `https://www.wizzair.com/en-gb/booking/select-flight/${job.src_code}/${job.dst_code}/${dateString}/null/1/0/0/null`;
};

const processJob = async (job) => {
    const url = getJobUrl(job, 0);

    await sleep(2, 3);
    const newTab = await chrome.tabs.create({url: url});
    const tabId = newTab.id;
    await attachDebugger(tabId);
    // await sendDebuggerCommand(tabId, 'Input.enable');
    await sendDebuggerCommand(tabId, 'Network.enable');
    // console.log('??????????', await sendDebuggerCommand(tabId, "Schema.getDomains"))

    await waitForLoad(tabId);
    console.log('Tab loaded.')

    // process job.days dates count, 0 is already loaded, so we start from 1
    for (let i = 1; i < job.days; i++) {
        await sleep(4, 3);
        // const center_xy = await getNextElementCenter(tabId, 'div.is-date-selected');
        // if (!center_xy) {
        //     console.warn('Could not find next flight-select element. Stopping date iteration');
        //     break;
        // }
        // await sendLeftClick(tabId, center_xy[0], center_xy[1]);
        await goTo(tabId, getJobUrl(job, i));
        await waitForLoad(tabId);
        console.log('Tab loaded.')
    }

    await sleep(2, 3);
};


setTimeout(async () => {
    // await sleep(2, 3);
    // const newTab = await chrome.tabs.create({
    //     url: 'https://www.wizzair.com/en-gb/booking/select-flight/WAW/CPH/2025-09-21/null/1/0/0/null'
    // });
    // await debuggerWithDomain(newTab.id, 'Input');
    // await debuggerWithDomain(newTab.id, 'Network');
    // listenWizzairNetworkEvents(newTab.id);
    // await waitForLoad(newTab.id);
    // console.log('Tab loaded.')
    // await sleep(4, 0);
    // console.log(await getAvailableDates(newTab.id));
    // // console.log(await getElementCenter(newTab.id, 'button[data-test="step-next-date"]'));
    listenWizzairNetworkEvents();
    await processJob({
        src_code: 'WAW',
        dst_code: 'ALC',
        start_date: '2025-09-25',
        days: 4,
    });
}, 0);
