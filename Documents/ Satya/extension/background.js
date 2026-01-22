// background.js

chrome.runtime.onInstalled.addListener(() => {
    chrome.contextMenus.create({
        id: "check-ai",
        title: "Check if AI-Generated",
        contexts: ["image"]
    });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
    if (info.menuItemId === "check-ai" && info.srcUrl) {
        // Send message to content script to show loading or process
        chrome.tabs.sendMessage(tab.id, {
            action: "analyze_image",
            srcUrl: info.srcUrl
        });
    }
});
