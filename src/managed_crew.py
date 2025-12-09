"""
Managed Crew - Orchestrates agents with Manager review/revision cycles.
Replaces the single run_analysis() with a managed flow.
"""
import os
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
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
from .manager_agent import (
    critique_agent_output,
    build_revision_prompt,
    RevisionHistory
)

MAX_REVISIONS = 2  # Maximum revision cycles per agent


def run_managed_analysis(ticker_input: str) -> dict:
    """
    Run equity analysis with Manager oversight and revision cycles.

    Returns:
        dict with keys:
            - ticker: str
            - final_report: str (CIO memo)
            - details: dict (each agent's final approved output)
            - revision_history: list (critique/revision records)
    """
    # 🧹 CLEANUP: Delete the Vector Database from previous runs
    for folder in ['.chroma', 'db']:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"   🧹 Cleared previous vector database: {folder}")

    print("### Welcome to the AI Investment Firm (Managed Mode) ###")

    # Get company name
    print(f"\n🔍 Fetching company name for {ticker_input}...")
    try:
        stock_info = yf.Ticker(ticker_input).info
        company_name = stock_info.get('longName') or stock_info.get('shortName') or ticker_input
    except Exception as e:
        print(f"   ⚠️ Could not fetch name, using ticker. Error: {e}")
        company_name = ticker_input

    print(f"   ✅ Identified: {company_name}")

    # Download 10-K data
    md_path = download_from_sec(ticker_input)
    if not md_path:
        md_path = download_from_google(ticker_input)

    if not md_path:
        if os.path.exists(f"downloads/{ticker_input}_10k.md"):
            md_path = f"downloads/{ticker_input}_10k.md"
            print(f"   ⚠️  Using cached file: {md_path}")
        else:
            raise FileNotFoundError(f"Could not find data for {ticker_input}. Please try again later.")

    # Initialize Tools
    print(f"\n⚙️  Loading {md_path} into Agent...")
    fundamental_tool = CustomMDXTool(
        mdx=md_path,
        config=dict(
            llm=dict(provider="openai", config=dict(model=MODEL_NAME)),
            embedder=dict(provider="openai", config=dict(model="text-embedding-3-small")),
        )
    )

    web_search_tool = BrowsingTool()
    stock_price_tool = TechnicalAnalysisTool()
    yf_fundamentals_tool = YFinanceFundamentalsTool()
    historical_financials_tool = HistoricalFinancialsTool()
    historical_price_tool = HistoricalPriceActionTool()

    # Store final outputs and revision histories
    approved_outputs = {}
    revision_histories = []

    # ========== PHASE 1: PARALLEL INDEPENDENT AGENTS ==========
    # Macro, Quant, and Technical can run in parallel (no dependencies)
    print("\n🚀 Phase 1: Running independent agents in parallel (Macro, Quant, Technical)...")

    # Define agent configurations
    macro_config = {
        "agent_config": {
            "role": "Macro & Sentiment Analyst",
            "goal": "Analyze macro-economic cycle and news sentiment.",
            "backstory": f"""You are a macroeconomist.
You specialize in tying macroeconomic conditions to potential stock performance.
You ONLY care about ways that macro factors impact {company_name} specifically.
You NEVER give generic industry analysis.""",
            "tools": [web_search_tool]
        },
        "task_description": f"""
Conduct a comprehensive macro analysis for **{company_name}** ({ticker_input}) using the PESTLE framework.

RESTRICTION: You must include the company name "{company_name}" in EVERY search query.
Do not search for generic terms like "industry sector".

Search Examples:
- "{company_name} regulatory risks 2025"
- "Interest rate impact 2025 relevant to sector of {company_name}"
- "{company_name} customer demand trends"

1. **Political/Legal:** Check for antitrust suits, trade wars, or new tariffs.
2. **Economic:** Analyze how current inflation/rate sensitivity impacts this specific sector.
3. **Social/Trends:** Look for shifts in consumer behavior SPECIFIC to this company's sector.
4. **Technological:** AI disruption or supply chain automation.

OUTPUT REQUIREMENT: Return a bulleted list for each PESTLE category, followed by a single "Macro Headwind Score" (0-10, where 10 is severe headwinds).
""",
        "expected_output": "Structured PESTLE analysis and a numerical Risk Score.",
        "company_name": company_name,
        "ticker": ticker_input
    }

    quant_config = {
        "agent_config": {
            "role": "Quantitative Analyst",
            "goal": "Retrieve accurate, up-to-date financial metrics.",
            "backstory": f"""You are a strict data auditor. You do not offer opinions, only verified data points.
You MUST use the provided tools to get the latest data for {company_name}.
If data is missing, you must state 'Data Unavailable' rather than guessing.""",
            "tools": [yf_fundamentals_tool, historical_financials_tool]
        },
        "task_description": f"""
CRITICAL: You MUST use the provided tools. Do not skip this step.
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
        "expected_output": "JSON summary of current metrics and historical trends.",
        "company_name": company_name,
        "ticker": ticker_input
    }

    technical_config = {
        "agent_config": {
            "role": "Technical Analyst",
            "goal": "Analyze price trends",
            "backstory": "You are a chartist.",
            "tools": [stock_price_tool, historical_price_tool]
        },
        "task_description": f"""
Conduct a technical analysis on {ticker_input}.

1. Use 'Get Technical Indicators' for current signals (RSI, SMA).
2. Use 'Get Price History' to analyze the last year's volatility.
   - Identify the month with the biggest drop.
   - Is the stock currently near its 52-week High or Low based on the monthly data?

OUTPUT REQUIREMENT:
Return a structured technical assessment combining current indicators with 1-year trend context.
""",
        "expected_output": "Technical report with support/resistance, RSI, and 1-year trend analysis.",
        "company_name": company_name,
        "ticker": ticker_input
    }

    # Run Macro, Quant, and Technical in parallel
    parallel_results = {}
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(run_agent_with_revisions, **macro_config): "Macro & Sentiment Analyst",
            executor.submit(run_agent_with_revisions, **quant_config): "Quantitative Analyst",
            executor.submit(run_agent_with_revisions, **technical_config): "Technical Analyst",
        }

        for future in as_completed(futures):
            agent_name = futures[future]
            try:
                output, history = future.result()
                parallel_results[agent_name] = (output, history)
                print(f"   ✅ {agent_name} completed")
            except Exception as e:
                print(f"   ❌ {agent_name} failed: {e}")
                parallel_results[agent_name] = (f"Error: {e}", RevisionHistory(agent_name))

    # Extract results
    macro_output, macro_history = parallel_results["Macro & Sentiment Analyst"]
    quant_output, quant_history = parallel_results["Quantitative Analyst"]
    technical_output, technical_history = parallel_results["Technical Analyst"]

    approved_outputs["Macro & Sentiment Analyst"] = macro_output
    approved_outputs["Quantitative Analyst"] = quant_output
    approved_outputs["Technical Analyst"] = technical_output
    revision_histories.append(macro_history.to_dict())
    revision_histories.append(quant_history.to_dict())
    revision_histories.append(technical_history.to_dict())

    # ========== PHASE 2: FUNDAMENTAL (depends on Quant) ==========
    print("\n🔍 Phase 2: Fundamental/Strategic Analysis (uses Quant output)")
    fundamental_output, fundamental_history = run_agent_with_revisions(
        agent_config={
            "role": "Fundamental Strategist",
            "goal": "Analyze the company's competitive moat and risks.",
            "backstory": f"""You synthesize financial data with strategic risks found in 10-K filings.
CRITICAL: If the 'Search 10-K Content' tool fails or returns no results,
you must state "No 10-K data available" and rely ONLY on the Quant data.
Never make up risk factors.""",
            "tools": [fundamental_tool]
        },
        task_description=f"""
Conduct a strategic analysis for {company_name} ({ticker_input}) based on 10-K filings.

**Context from Quantitative Analyst:**
{quant_output}

1. Search the MDX for 'Risk Factors' and 'Competition'.
2. Compare the 'Gross Margins' and 'Profit Margins' from the Quant data against the qualitative risks.
    - Example: If Margins are dropping (Quant), find the reason in the text (Qual).

OUTPUT REQUIREMENT:
A brief strategic report linking the numbers to the narrative.
""",
        expected_output="Strategic analysis linking financial ratios to text-based risks.",
        company_name=company_name,
        ticker=ticker_input
    )
    approved_outputs["Fundamental Strategist"] = fundamental_output
    revision_histories.append(fundamental_history.to_dict())

    # ========== PHASE 3: CIO SYNTHESIS (depends on all) ==========
    print("\n🎯 Phase 3: CIO Final Synthesis")
    cio_output, cio_history = run_cio_with_revisions(
        company_name=company_name,
        ticker=ticker_input,
        macro_output=macro_output,
        quant_output=quant_output,
        fundamental_output=fundamental_output,
        technical_output=technical_output
    )
    approved_outputs["Chief Investment Officer"] = cio_output
    revision_histories.append(cio_history.to_dict())

    return {
        "ticker": ticker_input,
        "final_report": cio_output,
        "details": approved_outputs,
        "revision_history": revision_histories
    }


def run_agent_with_revisions(agent_config: dict, task_description: str,
                              expected_output: str, company_name: str, ticker: str) -> tuple:
    """
    Run a single agent with Manager review/revision cycles.

    Returns:
        tuple: (final_output: str, revision_history: RevisionHistory)
    """
    role = agent_config["role"]
    history = RevisionHistory(role)
    current_task_description = task_description

    for iteration in range(1, MAX_REVISIONS + 1):
        print(f"   🔄 {role} - Iteration {iteration}")

        # Create agent and task
        agent = Agent(
            role=role,
            goal=agent_config["goal"],
            backstory=agent_config["backstory"],
            verbose=True,
            llm=MODEL_NAME,
            tools=agent_config["tools"]
        )

        task = Task(
            description=current_task_description,
            expected_output=expected_output,
            agent=agent
        )
        task.async_execution = False

        # Run single-agent crew
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True
        )

        result = crew.kickoff()
        output = result.raw if hasattr(result, 'raw') else str(result)

        # Manager critique
        print(f"   📝 Manager reviewing {role} output...")
        critique = critique_agent_output(role, output, company_name, ticker)
        history.add_iteration(output, critique, iteration)

        if critique["approved"]:
            print(f"   ✅ {role} output APPROVED")
            return output, history

        if iteration < MAX_REVISIONS:
            print(f"   🔄 {role} needs revision: {critique['critique'][:100]}...")
            current_task_description = build_revision_prompt(
                task_description,
                critique["revision_instructions"],
                output,
                iteration + 1
            )
        else:
            print(f"   ⚠️ {role} max revisions reached, using final output")

    return output, history


def run_cio_with_revisions(company_name: str, ticker: str, macro_output: str,
                            quant_output: str, fundamental_output: str, technical_output: str) -> tuple:
    """
    Run the CIO agent with Manager review/revision cycles.

    Returns:
        tuple: (final_output: str, revision_history: RevisionHistory)
    """
    role = "Chief Investment Officer"
    history = RevisionHistory(role)

    base_task_description = f"""
Synthesize the following MANAGER-APPROVED analyst reports to make a final decision for {company_name} ({ticker}).

---
**MACRO & SENTIMENT ANALYSIS:**
{macro_output}

---
**QUANTITATIVE ANALYSIS:**
{quant_output}

---
**FUNDAMENTAL/STRATEGIC ANALYSIS:**
{fundamental_output}

---
**TECHNICAL ANALYSIS:**
{technical_output}

---

Checks:
1. Did the Quant Analyst retrieve valid data? If not, state "Insufficient Data".
2. Do not hallucinate metrics. Use ONLY what is provided above.

**OUTPUT FORMAT (use these EXACT section headers):**

Recommendation
- Position: [Buy/Sell/Hold]
- Conviction Score: [X] / 10
- Kill Switch Price: [price] (use Technical Analyst's support level, or 5% below current price if not provided)
- Rationale: [1-2 sentence summary of why]

Executive Summary
[One paragraph synthesizing the key thesis, risks, and catalysts]

Macro & Sentiment
- Macro Headwind Score: [X/10]
- [Key macro factors from the Macro Analyst affecting this stock]

Quantitative Snapshot
- [Key metrics: Revenue, Margins, FCF, P/E, Growth rates]
- [3-year trends]

Fundamental Analysis
- [Moat and competitive positioning]
- [Key risks from 10-K]
- [Strategic concerns]

Technical Analysis
- Current Price: [price]
- Trend: [Bullish/Bearish/Neutral]
- Key Levels: [Support/Resistance]
- RSI: [value and interpretation]

Scenario Analysis
- Base Case: [target and probability]
- Bull Case: [target and probability]
- Bear Case: [target and probability]
- Probability-weighted expected return: [calculation]

Actionable Takeaways
- [Specific entry/exit conditions]
- [Position sizing guidance]
- [Key catalysts to monitor]

Data Caveats
- [List any missing data or assumptions made]

Do not give any explanations beyond the final memo. Use the EXACT section headers above.
"""

    current_task_description = base_task_description
    expected_output = "Final Investment Memo."

    for iteration in range(1, MAX_REVISIONS + 1):
        print(f"   🔄 {role} - Iteration {iteration}")

        cio = Agent(
            role="Chief Investment Officer",
            goal="Synthesize recommendation",
            backstory=f"""You are the CIO.
You must synthesize inputs from all analysts to make a final Buy/Sell/Hold recommendation for {company_name}.
You MUST NOT hallucinate data. If any required data is missing, SAY SO.
You can make a recommendation with the caveat that data is missing.""",
            expected_output="""Final Investment Memo including Recommendation, Conviction Score (state x out of 10), and Kill Switch Price.
If data is insufficient, state 'Insufficient Data' and do not provide a recommendation.
Give an executive summary of the recommendation and key reasons.
Then, elaborate. Provide a bulleted list of key points from each analyst supporting your decision.""",
            verbose=True,
            llm=MODEL_NAME,
            tools=[],
            allow_delegation=False
        )

        synthesis_task = Task(
            description=current_task_description,
            expected_output=expected_output,
            agent=cio
        )
        synthesis_task.async_execution = False

        crew = Crew(
            agents=[cio],
            tasks=[synthesis_task],
            process=Process.sequential,
            verbose=True
        )

        result = crew.kickoff()
        output = result.raw if hasattr(result, 'raw') else str(result)

        # Manager critique
        print(f"   📝 Manager reviewing {role} output...")
        critique = critique_agent_output(role, output, company_name, ticker)
        history.add_iteration(output, critique, iteration)

        if critique["approved"]:
            print(f"   ✅ {role} output APPROVED")
            return output, history

        if iteration < MAX_REVISIONS:
            print(f"   🔄 {role} needs revision: {critique['critique'][:100]}...")
            current_task_description = build_revision_prompt(
                base_task_description,
                critique["revision_instructions"],
                output,
                iteration + 1
            )
        else:
            print(f"   ⚠️ {role} max revisions reached, using final output")

    return output, history
