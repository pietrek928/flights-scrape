import { sleep } from './utils.js';
import { save_data } from './scheduler.js'
import { debuggerWithDomain } from './debug.js'



const connectionsUrl = 'Api/asset/map';
const datesUrl = 'Api/search/flightDates';
const detailsUrl = 'Api/search/search';


const listenWizzairNetworkEvents = (tabId) => {
    let postPayloads = {};
    chrome.debugger.onEvent.addListener((source, method, params) => {
        if (source.tabId === tabId) {
            handleDebugEvent(source, method, params, postPayloads);
        }
    });
};


const handleDebugEvent = (source, method, params, postPayloads) => {
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


const getElementText = async (tabId, cssSelector) => {
    return await runFunctionInTab(tabId, (selector) => {
        return Array.from(document.querySelectorAll(selector)).map(element => element.textContent);
    }, cssSelector);
};


const getAvailableDates = async (tabId) => {
    return await getElementText(tabId, '.column > .date');
};


setTimeout(async () => {
    await sleep(2, 3);
    const newTab = await chrome.tabs.create({
        url: 'https://www.wizzair.com/en-gb/booking/select-flight/WAW/CPH/2025-09-21/null/1/0/0/null'
    });
    await debuggerWithDomain(newTab.id, 'Network');
    listenWizzairNetworkEvents(newTab.id);
    await waitForLoad(newTab.id);
    console.log('Tab loaded.')
    await sleep(4, 0);
    console.log(await getAvailableDates(newTab.id));
    console.log(await getElementCenter(newTab.id, 'button[data-test="step-next-date"]'));
}, 0);
