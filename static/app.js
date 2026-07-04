const form = document.querySelector("#upload-form");
const progressPanel = document.querySelector("#progress-panel");
const progressLabel = document.querySelector("#progress-label");
const progressPercent = document.querySelector("#progress-percent");
const progressFill = document.querySelector("#progress-fill");

function setProgress(percent, label) {
    progressLabel.textContent = label || "Laeuft";
    progressPercent.textContent = `${percent}%`;
    progressFill.style.width = `${percent}%`;
}

async function pollStatus(jobId) {
    const response = await fetch(`/status/${jobId}`);
    const status = await response.json();

    if (!response.ok || status.status === "error") {
        setProgress(status.percent || 0, status.error || "Fehler");
        form.querySelector("button").disabled = false;
        return;
    }

    setProgress(status.percent, status.label);

    if (status.status === "done") {
        window.location.href = `/result/${jobId}`;
        return;
    }

    window.setTimeout(() => pollStatus(jobId), 700);
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const button = form.querySelector("button");
    button.disabled = true;
    progressPanel.hidden = false;
    setProgress(0, "Upload");

    const response = await fetch(form.action, {
        method: "POST",
        body: new FormData(form)
    });
    const payload = await response.json();

    if (!response.ok) {
        setProgress(0, payload.error || "Fehler");
        button.disabled = false;
        return;
    }

    pollStatus(payload.job_id);
});
