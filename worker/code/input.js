import { sleep } from './utils.js';


// debuggerWithDomain(tabId, 'Input')

export const sendLeftClick = async (tabId, x, y)  => {
    await sleep(.1, .05);

    await chrome.debugger.sendCommand({ tabId: tabId }, 'Input.dispatchMouseEvent', {
        type: 'mousePressed',
        x: x,
        y: y,
        button: 'left',
        clickCount: 1
    });

    await sleep(.1, .05);

    // Send a mouse up event to complete the click
    await chrome.debugger.sendCommand({ tabId: tabId }, 'Input.dispatchMouseEvent', {
        type: 'mouseReleased',
        x: x,
        y: y,
        button: 'left',
        clickCount: 1
    });
};

export const sendKeys = async (tabId, text) => {
    for (const char of text) {
        await sleep(.1, .05);
        await chrome.debugger.sendCommand({ tabId: tabId }, "Input.dispatchKeyEvent", {
            type: "keyDown",
            text: char
        });
        await sleep(.1, .05);
        await chrome.debugger.sendCommand({ tabId: tabId }, "Input.dispatchKeyEvent", {
            type: "keyUp",
            text: char
        });
    }
};
