/*
Config Import / Export Section
==============================

Handles importing HAProxy configuration from a file and
exporting the current configuration as text with copy support.
*/

/* Opens a file picker dialog and imports the selected HAProxy config file via the API */
async function importConfig() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.cfg,.conf,.txt';
    input.onchange = async e => {
        const file = e.target.files[0]; if (!file) return;
        const text = await file.text();
        try {
            await api('/api/config/import', { method: 'POST', body: JSON.stringify({ config_text: text }) });
            toast('Configuration imported!');
            switchSection('overview');
        } catch (err) { toast(err.message, 'error'); }
    };
    input.click();
}

/* Fetches the current HAProxy configuration text from the API and displays it in the export textarea */
async function exportConfig() {
    try {
        const d = await api('/api/config/export');
        document.getElementById('config-export-text').value = d.config_text || d;
    } catch (err) { toast(err.message, 'error'); }
}

/* Copies the exported configuration text to the clipboard */
function copyExport() {
    const ta = document.getElementById('config-export-text');
    navigator.clipboard.writeText(ta.value).then(() => toast('Copied to clipboard'));
}
