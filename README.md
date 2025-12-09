# Mosaic AI
The World's Greatest Team of Equity Analysts

An automated equity analysis tool powered by a multi-agent AI system. This project utilizes **CrewAI** to orchestrate a team of specialized AI agents that conduct comprehensive investment research, from macro-economic analysis to technical charting and fundamental 10-K reviews.

## 🚀 Features

*   **Multi-Agent Architecture:** Orchestrates 5 specialized agents:
    *   **Macro & Sentiment Analyst:** Conducts PESTLE analysis and news sentiment checks via web search.
    *   **Quantitative Analyst:** Audits financial metrics, margins, and growth trends using `yfinance`.
    *   **Fundamental Analyst:** Uses RAG to analyze SEC 10-K filings for qualitative risks and competitive advantages.
    *   **Technical Analyst:** Evaluates price action, volatility, and technical indicators (RSI, SMA).
    *   **Chief Investment Officer:** Synthesizes all findings into a final "Investment Memo" with a Buy/Sell/Hold recommendation.
*   **Automated Data Pipeline:**
    *   Fetches and caches SEC 10-K filings (converted to Markdown).
    *   Ingests reports into a vector database for RAG (Retrieval-Augmented Generation).
    *   Retrieves real-time market data and historical financials.
*   **Context-Aware Analysis:** Agents share context (e.g., Fundamental Analyst validates Quantitative findings against stated risks in the 10-K).

## 🛠️ Installation

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
    *   `OPENAI_MODEL_NAME`: The model to use (e.g., `gpt-4o`, `gpt-3.5-turbo`).

## 🏃 Usage

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

**Web Interface:**
To use the web-based dashboard and chat:
1.  Start the API server:
    ```bash
    uvicorn src.api:app --reload
    ```
2.  Open `frontend-web/index.html` in your browser.

## 📂 Project Structure

*   `main.py`: Entry point of the application. Handles CLI args and kicks off the Crew.
*   `src/`:
    *   `api.py`: FastAPI server for the web interface and chat functionality.
    *   `chat_service.py`: Implements the RAG-based chat feature for interacting with analysis reports.
    *   `config.py`: Configuration settings (Model names, API keys, etc.).
    *   `etl.py`: Scripts for downloading and processing SEC 10-K filings.
    *   `managed_crew.py`: Defines the agents, tasks, and overall crew orchestration logic.
    *   `manager_agent.py`: Contains the logic for the Manager Agent, responsible for critiquing and ensuring output quality.
    *   `mock_data.py`: Provides mock data for testing and development purposes.
    *   `tools.py`: Custom tools for the agents (Web Browsing, YFinance, Technical Analysis, RAG).
*   `downloads/`: Stores cached SEC 10-K markdown files.
*   `notes/`: Contains scratchpad files (e.g., `ideas.txt`, `memo.txt`, `outputs.txt`) for project development and documentation.

## ⚠️ Disclaimer

This tool is for educational and research purposes only. It does **not** constitute financial advice. Always conduct your own due diligence before making investment decisions.
