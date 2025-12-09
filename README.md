# Mosaic AI
The World's Greatest Team of Equity Analysts

An automated equity analysis tool powered by a multi-agent AI system. This project utilizes **CrewAI** to orchestrate a team of specialized AI agents that conduct comprehensive investment research, from macro-economic analysis to technical charting and fundamental 10-K reviews.

## Features

*   **Multi-Agent Architecture:** Orchestrates 5 specialized analyst agents with Manager oversight:
    *   **Macro & Sentiment Analyst:** Conducts PESTLE analysis and news sentiment checks via web search.
    *   **Quantitative Analyst:** Audits financial metrics, margins, and growth trends using `yfinance`.
    *   **Fundamental Strategist:** Uses RAG to analyze SEC 10-K filings for qualitative risks and competitive advantages, cross-referencing with quantitative data.
    *   **Technical Analyst:** Evaluates price action, volatility, and technical indicators (RSI, SMA).
    *   **Chief Investment Officer:** Synthesizes all findings into a final "Investment Memo" with a Buy/Sell/Hold recommendation.
    *   **Manager Agent:** Reviews and critiques each agent's output, requesting revisions when quality standards aren't met (up to 2 revision cycles per agent).
*   **Parallel Execution:** Independent agents (Macro, Quant, Technical) run in parallel for faster analysis, while dependent agents (Fundamental Strategist, CIO) run sequentially.
*   **Automated Data Pipeline:**
    *   Fetches and caches SEC 10-K filings (converted to Markdown).
    *   Ingests reports into a vector database (ChromaDB) for RAG (Retrieval-Augmented Generation).
    *   Retrieves real-time market data and historical financials.
*   **Interactive Chat:** After analysis completes, chat with an AI about the findings using RAG-powered Q&A (available in both CLI and web interface).
*   **Context-Aware Analysis:** Agents share context (e.g., Fundamental Strategist validates Quantitative findings against stated risks in the 10-K).

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/cmh32/equity-analyst.git
    cd equity-analyst
    ```

2.  **Install dependencies:**
    It is recommended to use a virtual environment.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3.  **Set up Environment Variables:**
    Copy the example environment file:
    ```bash
    cp .env.example .env
    ```
    Edit `.env` and add your API keys:
    *   `OPENAI_API_KEY`: Required for LLM and Embeddings.
    *   `SERPER_API_KEY`: Required for Google Search capabilities (Macro Agent).
    *   `OPENAI_MODEL_NAME`: (Optional) The model to use. Defaults to `gpt-4o`.

## Usage

Run the analysis by providing a stock ticker symbol.

**Command Line Argument:**
```bash
python main.py TSLA
```

**Interactive Mode:**
If you run it without arguments, you will be prompted to enter a ticker.
```bash
python main.py
# Enter the stock ticker (e.g., TSLA): NVDA
```

After the analysis completes, you'll enter an interactive chat mode where you can ask questions about the findings. The full analysis is also saved to a timestamped output file (e.g., `output_TSLA_20251209_123456.txt`).

**Web Interface:**
To use the web-based dashboard and chat:
1.  Start the API server:
    ```bash
    uvicorn src.api:app --reload
    ```
2.  Open `frontend-web/index.html` in your browser.

## Project Structure

```
.
├── main.py                 # Entry point - runs analysis and starts chat
├── requirements.txt        # Python dependencies
├── src/
│   ├── api.py              # FastAPI server for web interface
│   ├── chat_service.py     # RAG-based chat for interacting with reports
│   ├── config.py           # Configuration (model names, API settings)
│   ├── etl.py              # Downloads and processes SEC 10-K filings
│   ├── managed_crew.py     # Agent definitions and crew orchestration
│   ├── manager_agent.py    # Manager Agent for quality control/revisions
│   ├── mock_data.py        # Mock data for testing
│   └── tools.py            # Custom tools (Web Search, YFinance, RAG, etc.)
├── frontend-web/           # Web dashboard (HTML/CSS/JS)
│   ├── index.html
│   ├── app.js
│   └── style.css
├── downloads/              # Cached SEC 10-K markdown files
├── data/                   # Additional data storage
└── notes/                  # Development notes and scratchpad
```

## Disclaimer

This tool is for educational and research purposes only. It does **not** constitute financial advice. Always conduct your own due diligence before making investment decisions.
