// content.js

function createBadge(x, y, score) {
    const badge = document.createElement("div");
    badge.innerText = score > 0.5 ? "⚠️ AI" : "✅ Real";
    badge.style.position = "absolute";
    badge.style.left = `${x}px`;
    badge.style.top = `${y}px`;
    badge.style.backgroundColor = score > 0.5 ? "red" : "green";
    badge.style.color = "white";
    badge.style.padding = "5px 10px";
    badge.style.borderRadius = "20px";
    badge.style.zIndex = "10000";
    badge.style.fontWeight = "bold";
    badge.style.boxShadow = "0 2px 5px rgba(0,0,0,0.2)";
    document.body.appendChild(badge);

    setTimeout(() => badge.remove(), 5000);
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "analyze_image") {
        console.log("Analyzing image:", request.srcUrl);

        // Mock API call to local backend
        // In a real extension, we would fetch(request.srcUrl) to get blob and send to backend
        // For now, we simulate a check

        alert("Analyzing image... Check console for details.");

        // Simulating result
        setTimeout(() => {
            const isFake = Math.random() > 0.5;
            alert(isFake ? "Warning: High probability of being AI-Generated!" : "Looks real.");
        }, 1500);
    }
});
