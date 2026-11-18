(() => {
  "use strict";

  const statusDot = document.getElementById("statusDot");
  const statusText = document.getElementById("statusText");

  if (!statusDot || !statusText) return;

  // ---------------------------------------------------------------------
  // AI status check
  // ---------------------------------------------------------------------
  async function checkHealth() {
    try {
      const res = await fetch("/health");
      const data = await res.json();
      if (data.status === "ok") {
        statusDot.className = "status-dot online";
        statusText.textContent = `AI Online \u00b7 ${data.device.toUpperCase()}`;
      } else {
        statusDot.className = "status-dot";
        statusText.textContent = "Loading models\u2026";
        setTimeout(checkHealth, 2500);
      }
    } catch (err) {
      statusDot.className = "status-dot offline";
      statusText.textContent = "AI Offline";
    }
  }
  checkHealth();
})();
