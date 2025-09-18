export const sleep = (base_s = 2., rand_s = 5.) => new Promise(
    (resolve) => setTimeout(resolve, (base_s + Math.random() * rand_s) * 1e3)
);

export const init_iframe = () => {
    const iframe = document.createElement('iframe');
    iframe.style.display = 'none';
    document.body.appendChild(iframe);
    return iframe;
}

export const execute_in_iframe = (iframe, func) => {
    const iframe_window = iframe.contentWindow;
    const iframe_document = iframe_window.document;
    const iframe_div = iframe_document.createElement('div');
    iframe_div.addEventListener('click', func);
    iframe_div.click();
};
