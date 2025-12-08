const API_URL = "http://localhost:8000";

let currentData = null;

async function analyzeStock() {
    const ticker = document.getElementById('tickerInput').value.trim();
    if (!ticker) return;

    // UI Reset
    document.getElementById('loading').classList.remove('hidden');
    document.getElementById('results').classList.add('hidden');
    document.getElementById('error').classList.add('hidden');
    document.getElementById('analyzeBtn').disabled = true;

    try {
        const response = await fetch(`${API_URL}/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ticker: ticker })
        });

        if (!response.ok) {
            throw new Error(`Server Error: ${response.statusText}`);
        }

        const data = await response.json();
        currentData = data;
        renderDashboard(data);

    } catch (err) {
        const errorDiv = document.getElementById('error');
        errorDiv.textContent = `Error: ${err.message}`;
        errorDiv.classList.remove('hidden');
    } finally {
        document.getElementById('loading').classList.add('hidden');
        document.getElementById('analyzeBtn').disabled = false;
    }
}

function renderDashboard(data) {
    const resultsSection = document.getElementById('results');
    const agentList = document.getElementById('agentList');
    const tickerTag = document.getElementById('tickerTag');

    resultsSection.classList.remove('hidden');
    tickerTag.textContent = data.ticker;
    agentList.innerHTML = ''; // Clear previous

    // 1. Add Final Report Option (Default)
    const finalItem = document.createElement('li');
    finalItem.textContent = "Final Investment Memo";
    finalItem.classList.add('active');
    finalItem.onclick = () => showReport('Final Investment Memo', data.final_report, finalItem);
    agentList.appendChild(finalItem);

    // 2. Add other agents
    if (data.details) {
        for (const [agentName, reportContent] of Object.entries(data.details)) {
            if (agentName === 'Chief Investment Officer') continue;
            const item = document.createElement('li');
            item.textContent = agentName;
            item.onclick = () => showReport(agentName, reportContent, item);
            agentList.appendChild(item);
        }
    }

    // Show final report by default
    showReport('Final Investment Memo', data.final_report, finalItem);
}

function showReport(title, content, activeElement) {
    // Update active state in sidebar
    document.querySelectorAll('.sidebar li').forEach(li => li.classList.remove('active'));
    activeElement.classList.add('active');

    // Render content
    document.getElementById('reportTitle').textContent = title;
    // Use marked library to parse Markdown
    document.getElementById('reportContent').innerHTML = marked.parse(content);
}
