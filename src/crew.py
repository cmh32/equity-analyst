import os
import shutil
import yfinance as yf
from crewai import Agent, Task, Crew, Process
from .config import MODEL_NAME
from .etl import download_from_sec, download_from_google
from .tools import (
    BrowsingTool,
    TechnicalAnalysisTool,
    YFinanceFundamentalsTool,
    HistoricalFinancialsTool,
    HistoricalPriceActionTool,
    CustomMDXTool,
)

def run_analysis(ticker_input: str):
    # 🧹 CLEANUP: Delete the Vector Database from previous runs
    # CrewAI/ChromaDB usually stores data in a folder named 'db' or '.chroma'
    for folder in ['.chroma', 'db']:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"   🧹 Cleared previous vector database: {folder}")

    print("### Welcome to the AI Investment Firm ###")

    print(f"\n🔍 Fetching company name for {ticker_input}...")
    try:
        stock_info = yf.Ticker(ticker_input).info
        # specific fallback: 'longName' is best for search, 'shortName' is backup
        company_name = stock_info.get('longName') or stock_info.get('shortName') or ticker_input
    except Exception as e:
        print(f"   ⚠️ Could not fetch name, using ticker. Error: {e}")
        company_name = ticker_input

    print(f"   ✅ Identified: {company_name}")

    # 1. Download Data
    md_path = download_from_sec(ticker_input)
    if not md_path:
        md_path = download_from_google(ticker_input)

    # Cache check / Fallback
    if not md_path:
        if os.path.exists(f"downloads/{ticker_input}_10k.md"):
            md_path = f"downloads/{ticker_input}_10k.md"
            print(f"   ⚠️  Using cached file: {md_path}")
        else:
            raise FileNotFoundError(f"Could not find data for {ticker_input}. Please try again later.")

    # 2. Initialize Tools
    print(f"\n⚙️  Loading {md_path} into Agent...")

    try:
        fundamental_tool = CustomMDXTool(
            mdx=md_path,
            config=dict(
                llm=dict(
                    provider="openai",
                    config=dict(model=MODEL_NAME),
                ),
                embedder=dict(
                    provider="openai",
                    config=dict(model="text-embedding-3-small"),
                ),
            )
        )
    except Exception as e:
        print(f"❌ Error initializing MDX Tool: {e}")
        # If MDX fails (likely embedding cost/error), we stop to save credits
        raise e

    web_search_tool = BrowsingTool()
    stock_price_tool = TechnicalAnalysisTool()
    yf_fundamentals_tool = YFinanceFundamentalsTool()
    historical_financials_tool = HistoricalFinancialsTool()
    historical_price_tool = HistoricalPriceActionTool()

    # 3. Agents

    macro_sentiment_analyst = Agent(
        role="Macro & Sentiment Analyst",
        goal="Analyze macro-economic cycle and news sentiment",
        backstory="You are a macroeconomist.",
        verbose=True,
        llm=MODEL_NAME,
        tools=[web_search_tool]
    )

    quant_analyst = Agent(
        role="Quantitative Analyst",
        goal="Retrieve accurate, up-to-date financial metrics.",
        backstory="You are a strict data auditor. You do not offer opinions, only verified data points.",
        verbose=True,
        llm=MODEL_NAME,
        tools=[yf_fundamentals_tool, historical_financials_tool]
    )

    fundamental_analyst = Agent(
        role="Fundamental Strategist",
        goal="Analyze the company's competitive moat and risks.",
        backstory="""You synthesize financial data with strategic risks found in 10-K filings.
        CRITICAL: If the 'Search 10-K Content' tool fails or returns no results,
        you must state "No 10-K data available" and rely ONLY on the Quant data.
        Never make up risk factors.""",
        verbose=True,
        llm=MODEL_NAME,
        tools=[fundamental_tool]
    )

    technical_analyst = Agent(
        role="Technical Analyst",
        goal="Analyze price trends",
        backstory="You are a chartist.",
        verbose=True,
        llm=MODEL_NAME,
        tools=[stock_price_tool, historical_price_tool]
    )

    chief_investment_officer = Agent(
        role="Chief Investment Officer",
        goal="Synthesize recommendation",
        backstory="You are the CIO.",
        verbose=True,
        llm=MODEL_NAME,
        tools=[],
        allow_delegation=False
    )

    # 4. Tasks

    macro_task = Task(
        description=f"""
        Conduct a comprehensive macro analysis for **{company_name}** ({ticker_input}) using the PESTLE framework.

        RESTRICTION: You must include the company name "{company_name}" in EVERY search query.
        Do not search for generic terms like "industry sector".

        Search Examples (feel free to ask questions beyond these examples, but ALWAYS include the company name):
        - "{company_name} regulatory risks 2025"
        - "Interest rate impact 2025 relevant to sector of {company_name}" (NOT just "interest rates")
        - "{company_name} customer demand trends"

        1. **Political/Legal:** Check for antitrust suits, trade wars, or new tariffs.
        2. **Economic:** Analyze how current inflation/rate sensitivity impacts this specific sector.
        3. **Social/Trends:** Look for shifts in consumer behavior SPECIFIC to energy/utilities (e.g., EV adoption, solar at home).
           (Do NOT mention unrelated trends like food/drugs).
        4. **Technological:** AI disruption or supply chain automation.

        OUTPUT REQUIREMENT: Return a bulleted list for each PESTLE category, followed by a single "Macro Headwind Score" (0-10, where 10 is severe headwinds).
        """,
        expected_output="Structured PESTLE analysis and a numerical Risk Score.",
        agent=macro_sentiment_analyst
    )

    quant_task = Task(
        description=f"""
        1. Fetch the latest financial metrics for {ticker_input} using 'Get Financial Metrics'.
        2. Fetch the historical financial statements using 'Get Historical Financials'.

        ANALYSIS REQUIRED:
        - Calculate the Revenue CAGR (Compound Annual Growth Rate) over the available period.
        - Check if Gross Margins are expanding or contracting over the last 3 years.
        - Is Free Cash Flow positive and growing?

        OUTPUT REQUIREMENT:
        Return a JSON summary including:
        - Current Ratios (P/E, etc.)
        - 3-Year Revenue Growth Trend (Rising/Falling)
        - 3-Year Margin Trend
        You must use ONLY the data provided in the latest financial metrics and historical financial statements.
        """,
        expected_output="JSON summary of current metrics and historical trends.",
        agent=quant_analyst
    )

    fundamental_strategy_task = Task(
        description=f"""
        Conduct a comprehensive macro analysis for {company_name} ({ticker_input}) using the PESTLE framework.
        1. Search the MDX for 'Risk Factors' and 'Competition'.
        2. Compare the 'Gross Margins' and 'Profit Margins' from the Quant data against the qualitative risks.
            - Example: If Margins are dropping (Quant), finds the reason in the text (Qual).

        OUTPUT REQUIREMENT:
        A brief strategic report linking the numbers to the narrative.
        """,
        expected_output="Strategic analysis linking financial ratios to text-based risks.",
        agent=fundamental_analyst,
        context=[quant_task]
    )

    technical_task = Task(
        description=f"""
        Conduct a technical analysis on {ticker_input}.

        1. Use 'Get Technical Indicators' for current signals (RSI, SMA).
        2. Use 'Get Price History' to analyze the last year's volatility.
           - Identify the month with the biggest drop.
           - Is the stock currently near its 52-week High or Low based on the monthly data?

        OUTPUT REQUIREMENT:
        Return a structured technical assessment combining current indicators with 1-year trend context.
        """,
        expected_output="Technical report with support/resistance, RSI, and 1-year trend analysis.",
        agent=technical_analyst
    )

    recommendation_task = Task(
        description="""
        Synthesize the reports to make a final decision.

        Checks:
        1. Did the Quant Analyst retrieve valid data? If not, state "Insufficient Data" and declare that you cannot make a recommendation.
        2. Do not hallucinate metrics. Use ONLY what is provided in the context.

        Determine:
        - Recommendation (Buy/Sell/Hold)
        - Conviction Score (0-10)
        - Kill Switch Price

        Do not give any explanations beyond the final memo or ask for more information.
        """,
        expected_output="Final Investment Memo.",
        agent=chief_investment_officer,
        context=[macro_task, quant_task, fundamental_strategy_task, technical_task]
    )

    # Async execution configuration
    macro_task.async_execution = True
    quant_task.async_execution = True
    technical_task.async_execution = True
    
    # Dependent tasks
    fundamental_strategy_task.async_execution = False
    recommendation_task.async_execution = False

    # 5. Kickoff
    stock_analysis_crew = Crew(
        agents=[
            macro_sentiment_analyst,
            quant_analyst,
            fundamental_analyst,
            technical_analyst,
            chief_investment_officer
        ],
        tasks=[
            macro_task,
            quant_task,
            fundamental_strategy_task,
            technical_task,
            recommendation_task
        ],
        process=Process.sequential,
        verbose=True
    )

    print("\n🤖 Agents are analyzing...")
    result = stock_analysis_crew.kickoff(inputs={"ticker": ticker_input})
    return result
