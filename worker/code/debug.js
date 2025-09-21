export const attachDebugger = async (tabId, api_version = "1.3") => {
    return new Promise((resolve, reject) => {
        chrome.debugger.attach({ tabId: tabId }, api_version, () => {
            if (chrome.runtime.lastError) {
                return reject(chrome.runtime.lastError.message);
            }
            console.log(`Debugger attached to tab ${tabId}.`);
            resolve();
        });
    });
};

export const sendDebuggerCommand = async (tabId, command) => {
    return new Promise((resolve, reject) => {
        chrome.debugger.sendCommand({ tabId: tabId }, command, {}, (result) => {
            if (chrome.runtime.lastError) {
                return reject(chrome.runtime.lastError.message);
            }
            console.log(`'${command}' command complete. Result:`, result);
            return resolve(result); // Resolve the promise here
        });
    });
};

// Input
// Network
export const debuggerWithDomain = async (tabId, domain) => {
    await attachDebugger(tabId);
    await sendDebuggerCommand(tabId, `${domain}.enable`);
};
