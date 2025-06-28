// For Admin Page
function updateUsage() {
    const canId = document.getElementById('adminCanIdInput').value.trim();
    const count = document.getElementById('adminCountInput').value;
    const resultDiv = document.getElementById('adminResult');
    if (!canId || count === '') {
        resultDiv.innerHTML = '<span class="bad">Please enter both ID and count.</span>';
        return;
    }
    fetch('/api/update_usage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ can_id: canId, count: count })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            resultDiv.innerHTML = '<span class="good">Usage updated successfully!</span>';
        } else {
            resultDiv.innerHTML = `<span class="bad">${data.msg || 'Failed to update.'}</span>`;
        }
    })
    .catch(() => {
        resultDiv.innerHTML = '<span class="bad">Error updating usage.</span>';
    });
}

// Allow Enter key to trigger actions
window.onload = () => {
    const adminCanIdInput = document.getElementById('adminCanIdInput');
    const adminCountInput = document.getElementById('adminCountInput');
    if (adminCanIdInput && adminCountInput) {
        adminCountInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') updateUsage();
        });
    }
};
