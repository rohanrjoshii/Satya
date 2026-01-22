document.getElementById('scanPageBtn').addEventListener('click', () => {
    document.getElementById('status').innerText = "Scanning page...";
    // Logic to message active tab to highlight all images
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        chrome.scripting.executeScript({
            target: { tabId: tabs[0].id },
            function: () => {
                const imgs = document.getElementsByTagName('img');
                for (let img of imgs) {
                    img.style.border = "2px solid blue";
                }
                alert(`Found ${imgs.length} images. Right click specific images to analyze.`);
            }
        });
    });
});
