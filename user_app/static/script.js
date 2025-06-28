// For User Page
function checkUsage() {
    const canId = document.getElementById('canIdInput').value.trim();
    const resultDiv = document.getElementById('result');
    if (!canId) {
        resultDiv.innerHTML = '<span class="bad">Please enter a Water Can ID.</span>';
        return;
    }
    fetch('/api/get_usage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ can_id: canId })
    })
    .then(res => {
        if (!res.ok) throw res;
        return res.json();
    })
    .then(data => {
        resultDiv.innerHTML = `Usage Count: <b>${data.count}</b><br>Status: <span class="${data.status.toLowerCase()}">${data.status}</span>`;
    })
    .catch(async err => {
        let msg = 'Water Can not found.';
        try { msg = (await err.json()).msg || msg; } catch {}
        resultDiv.innerHTML = `<span class="bad">${msg}</span>`;
    });
}

// Allow Enter key to trigger actions
window.onload = () => {
    const canIdInput = document.getElementById('canIdInput');
    if (canIdInput) {
        canIdInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') checkUsage();
        });
    }
};
