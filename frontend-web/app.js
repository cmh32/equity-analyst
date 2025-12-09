const API_URL = "http://localhost:8000";
const TEST_MODE = true; // Set to false to use real API

let currentData = null;
let parsedSections = null;
let chatHistory = [];

// Mock data for testing without backend
const MOCK_DATA = {
    ticker: "AAPL",
    final_report: `########################
## FINAL INVESTMENT MEMO ##
########################

Apple Inc. (AAPL) – Final Investment Memo (Revision 3)

Recommendation
- Position: HOLD
- Conviction Score: 6.5 / 10
- Kill Switch Price: 269.50 (Close below 269.50 triggers exit)
- Rationale at a glance: The corrected macro-driven upside (via a probability-weighted ER of ~5.3%) supports a constructive view on Apple's long-run cash-generation and moat, but near-term regulatory, geopolitical, and cross-border cost risks cap enthusiasm.

Executive Summary (one paragraph)
Apple's earnings power remains durable with expanding margins and robust free cash flow, backed by a large ecosystem and Services upside. Yet, near-term headwinds from antitrust/DMA regulation, tariff/geopolitical frictions, and China exposure justify a cautious stance.

Macro & Sentiment (Macro Headwind Score: 7.0 / 10)
Macro Headwind Score: 7.0
- Political / Legal (weight 0.28; Sub-score 8.0)
  - Data points: DOJ antitrust action trajectory (2024–2025); EU DMA enforcement and potential remedies.
- Economic (weight 0.22; Sub-score 7.0)
  - Data points: 3-year revenue CAGR of 1.82% and a hardware cycle sensitive to higher financing costs.
- Social (weight 0.14; Sub-score 6.5)
  - Data points: Brand strength supports pricing; Services growth diversifies mix.

Quantitative / Fundamental Snapshot (as of 2025-09-30)
- Revenue (FY2025): 416.161B
- Gross Margin (FY2025): 46.91%
- Operating Margin (FY2025): 31.90%
- Net Margin (FY2025): 26.90%
- Free Cash Flow (FY2025): 98.767B
- Trailing P/E: 37.20x; Forward P/E: 33.44x

Scenario Analysis (quantified where possible)
Baseline (FY2025)
- Revenue: 416.161B
- GM: 46.91% → Gross Profit ≈ 194.9B

Scenario 1: 50 bps Gross Margin compression
- GM 46.41% (−0.50pp); Net Income delta: roughly −1.9 to −2.5B

Technical Analysis (as of latest monthly close)
- Current price: 277.89
- Momentum: RSI(14) 66.46 (bullish but not overbought)
- Breakout level: Resistance at 288.62 (52-week high)
- Kill Switch: 269.50 (exit level on daily close)

Actionable Takeaways (CIO synthesis)
- Core stance: HOLD. Apple remains a high-quality compounder with durable cash flow.
- Price action playbook:
  - If price closes above 288.62 on strong volume: consider scaling into a long
  - If price retraces toward 218–221: consider a pullback entry

Notes on data hygiene and caveats
- Data gaps acknowledged: precise Greater China revenue share; Services revenue/margin by year; diluted EPS.

Citations and anchor points (for audit)
- Apple 2025 Form 10-K – reference for revenue mix and risk disclosures
- DOJ antitrust actions and EU DMA enforcement (2024–2025)`,
    details: {},
    revision_history: []
};

// Section definitions for parsing CIO memo (matching exact headers from CIO prompt)
const SECTION_PATTERNS = [
    { key: 'recommendation', title: 'Recommendation', pattern: /^Recommendation\s*$/im },
    { key: 'executive_summary', title: 'Executive Summary', pattern: /^Executive Summary\s*$/im },
    { key: 'macro_sentiment', title: 'Macro & Sentiment', pattern: /^Macro & Sentiment\s*$/im },
    { key: 'quantitative', title: 'Quantitative Snapshot', pattern: /^Quantitative Snapshot\s*$/im },
    { key: 'fundamental', title: 'Fundamental Analysis', pattern: /^Fundamental Analysis\s*$/im },
    { key: 'technical', title: 'Technical Analysis', pattern: /^Technical Analysis\s*$/im },
    { key: 'scenario_analysis', title: 'Scenario Analysis', pattern: /^Scenario Analysis\s*$/im },
    { key: 'actionable', title: 'Actionable Takeaways', pattern: /^Actionable Takeaways\s*$/im },
    { key: 'caveats', title: 'Data Caveats', pattern: /^Data Caveats\s*$/im }
];

async function analyzeStock() {
    const ticker = document.getElementById('tickerInput').value.trim();
    if (!ticker) return;

    // UI Reset
    document.getElementById('loading').classList.remove('hidden');
    document.getElementById('results').classList.add('hidden');
    document.getElementById('error').classList.add('hidden');
    document.getElementById('analyzeBtn').disabled = true;

    try {
        let data;

        if (TEST_MODE) {
            // Use mock data for testing
            await new Promise(r => setTimeout(r, 500)); // Simulate delay
            data = { ...MOCK_DATA, ticker: ticker.toUpperCase() };
        } else {
            const response = await fetch(`${API_URL}/analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ticker: ticker })
            });

            if (!response.ok) {
                let errorMessage = `Server Error: ${response.statusText}`;
                try {
                    const errorData = await response.json();
                    if (errorData.detail) {
                        errorMessage = errorData.detail;
                    }
                } catch (e) {
                    // If response is not JSON, fall back to statusText
                }
                throw new Error(errorMessage);
            }

            data = await response.json();
        }

        currentData = data;
        parsedSections = parseCIOSections(data.final_report);
        chatHistory = []; // Reset chat history for new analysis
        renderDashboard(data, parsedSections);

    } catch (err) {
        const errorDiv = document.getElementById('error');
        errorDiv.textContent = `Error: ${err.message}`;
        errorDiv.classList.remove('hidden');
    } finally {
        document.getElementById('loading').classList.add('hidden');
        document.getElementById('analyzeBtn').disabled = false;
    }
}

/**
 * Parse CIO memo into sections based on header patterns
 */
function parseCIOSections(content) {
    const sections = {};
    const lines = content.split('\n');

    // Find section boundaries
    const sectionStarts = [];

    for (const sectionDef of SECTION_PATTERNS) {
        for (let i = 0; i < lines.length; i++) {
            if (sectionDef.pattern.test(lines[i])) {
                sectionStarts.push({
                    key: sectionDef.key,
                    title: sectionDef.title,
                    lineIndex: i
                });
                break;
            }
        }
    }

    // Sort by line index
    sectionStarts.sort((a, b) => a.lineIndex - b.lineIndex);

    // Extract content for each section
    for (let i = 0; i < sectionStarts.length; i++) {
        const start = sectionStarts[i].lineIndex;
        const end = (i + 1 < sectionStarts.length) ? sectionStarts[i + 1].lineIndex : lines.length;

        sections[sectionStarts[i].key] = {
            title: sectionStarts[i].title,
            content: lines.slice(start, end).join('\n').trim()
        };
    }

    // Extract key metrics from full content (more reliable)
    sections.metrics = extractKeyMetrics(content);

    return sections;
}

/**
 * Extract key metrics from the full report content
 * Searches entire content since format varies
 */
function extractKeyMetrics(content) {
    const metrics = {
        position: 'N/A',
        conviction: 'N/A',
        killSwitch: 'N/A'
    };

    // Position: HOLD, BUY, SELL (multiple formats)
    // Format 1: "Position: HOLD" or "- Position: HOLD"
    // Format 2: "Recommendation: Hold"
    const positionMatch = content.match(/(?:Position|Recommendation)[\s:]*-?\s*(HOLD|BUY|SELL|STRONG BUY|STRONG SELL)/i);
    if (positionMatch) metrics.position = positionMatch[1].toUpperCase();

    // Conviction Score (multiple formats)
    // Format 1: "Conviction Score: 6.5 / 10"
    // Format 2: "Conviction Score: 6"
    const convictionMatch = content.match(/Conviction\s*(?:Score)?[\s:]*(\d+(?:\.\d+)?)\s*(?:\/\s*10)?/i);
    if (convictionMatch) metrics.conviction = convictionMatch[1];

    // Kill Switch Price (multiple formats)
    // Format 1: "Kill Switch Price: 269.50"
    // Format 2: "Kill Switch: 964.17"
    const killMatch = content.match(/Kill\s*Switch(?:\s*Price)?[\s:]*\$?([\d,.]+)/i);
    if (killMatch) metrics.killSwitch = killMatch[1].replace(/,/g, '');

    return metrics;
}

/**
 * Get color class for position
 */
function getPositionColor(position) {
    switch (position.toUpperCase()) {
        case 'BUY':
        case 'STRONG BUY':
            return 'position-buy';
        case 'SELL':
        case 'STRONG SELL':
            return 'position-sell';
        default:
            return 'position-hold';
    }
}

function renderDashboard(data, sections) {
    const resultsSection = document.getElementById('results');
    const sectionList = document.getElementById('agentList');
    const tickerTag = document.getElementById('tickerTag');
    const summaryCard = document.getElementById('summaryCard');

    resultsSection.classList.remove('hidden');
    tickerTag.textContent = data.ticker;
    sectionList.innerHTML = '';

    // Render summary card
    if (sections.metrics) {
        const m = sections.metrics;
        summaryCard.innerHTML = `
            <div class="metric">
                <span class="metric-label">Position</span>
                <span class="metric-value ${getPositionColor(m.position)}">${m.position}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Conviction</span>
                <span class="metric-value">${m.conviction}<span class="metric-unit">/10</span></span>
            </div>
            <div class="metric">
                <span class="metric-label">Kill Switch</span>
                <span class="metric-value">$${m.killSwitch}</span>
            </div>
        `;
        summaryCard.classList.remove('hidden');
    }

    // Add "Full Memo" option first
    const fullItem = document.createElement('li');
    fullItem.textContent = "Full Memo";
    fullItem.onclick = () => showReport('Full Investment Memo', data.final_report, fullItem);
    sectionList.appendChild(fullItem);

    // Add divider
    const divider = document.createElement('li');
    divider.className = 'divider';
    divider.textContent = 'Sections';
    sectionList.appendChild(divider);

    // Add section items
    let firstSection = null;
    for (const sectionDef of SECTION_PATTERNS) {
        if (sections[sectionDef.key]) {
            const item = document.createElement('li');
            item.textContent = sections[sectionDef.key].title;
            item.onclick = () => showReport(
                sections[sectionDef.key].title,
                sections[sectionDef.key].content,
                item
            );
            sectionList.appendChild(item);
            if (!firstSection) firstSection = item;
        }
    }

    // Show recommendation section by default
    if (sections.recommendation) {
        firstSection.classList.add('active');
        showReport(sections.recommendation.title, sections.recommendation.content, firstSection);
    }
}

function showReport(title, content, activeElement) {
    // Update active state in sidebar
    document.querySelectorAll('.sidebar li').forEach(li => {
        if (!li.classList.contains('divider')) {
            li.classList.remove('active');
        }
    });
    if (activeElement) activeElement.classList.add('active');

    // Render content
    document.getElementById('reportTitle').textContent = title;
    // Remove ~~ markers entirely to prevent strikethrough rendering
    const sanitizedContent = content.replace(/~~/g, '');
    
    const reportContent = document.getElementById('reportContent');
    if (typeof marked !== 'undefined' && marked.parse) {
        reportContent.innerHTML = marked.parse(sanitizedContent);
    } else {
        // Fallback if marked is not loaded
        reportContent.textContent = sanitizedContent;
        console.warn('Marked.js not loaded, falling back to plain text');
    }

    // Show chat section
    const chatSection = document.getElementById('chatSection');
    chatSection.classList.remove('hidden');
}

/**
 * Send a chat message and get RAG response
 */
async function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const question = input.value.trim();

    if (!question || !currentData) return;

    const sendBtn = document.getElementById('chatSendBtn');

    // Add user message to UI
    appendChatMessage('user', question);
    input.value = '';
    sendBtn.disabled = true;

    // Add to history
    chatHistory.push({ role: 'user', content: question });

    try {
        if (TEST_MODE) {
            // Mock response for testing
            await new Promise(r => setTimeout(r, 500));
            const mockResponse = `This is a mock response about ${currentData.ticker}. In production, this would use RAG to search the analysis.`;
            appendChatMessage('assistant', mockResponse);
            chatHistory.push({ role: 'assistant', content: mockResponse });
        } else {
            const response = await fetch(`${API_URL}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ticker: currentData.ticker,
                    question: question,
                    history: chatHistory.slice(-6) // Send last 6 messages for context
                })
            });

            if (!response.ok) {
                throw new Error(`Chat Error: ${response.statusText}`);
            }

            const data = await response.json();
            appendChatMessage('assistant', data.response);
            chatHistory.push({ role: 'assistant', content: data.response });
        }
    } catch (err) {
        console.error("Chat Error:", err);
        appendChatMessage('assistant', `Error: ${err.message}`);
    } finally {
        sendBtn.disabled = false;
        input.focus();
    }
}

/**
 * Append a message to the chat UI
 */
function appendChatMessage(role, content) {
    const messagesDiv = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${role}`;

    const labelSpan = document.createElement('span');
    labelSpan.className = 'chat-label';
    labelSpan.textContent = role === 'user' ? 'You' : 'AI';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'chat-content';
    
    if (typeof marked !== 'undefined' && marked.parse) {
        contentDiv.innerHTML = marked.parse(content);
    } else {
        contentDiv.textContent = content;
    }

    messageDiv.appendChild(labelSpan);
    messageDiv.appendChild(contentDiv);
    messagesDiv.appendChild(messageDiv);

    // Scroll to bottom
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// Allow Enter key to send chat
document.addEventListener('DOMContentLoaded', () => {
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendChatMessage();
            }
        });
    }
});
