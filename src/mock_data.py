"""
Mock data for troubleshooting the chatbot without running full analysis.
"""

def get_mock_analysis(ticker: str) -> dict:
    ticker = ticker.upper()
    return {
        "ticker": ticker,
        "final_report": f"""
Recommendation
- Position: Buy
- Conviction Score: 8/10
- Kill Switch Price: 100.00
- Rationale: Strong growth potential and solid fundamentals.

Executive Summary
{ticker} is showing strong signs of growth. The company has a solid balance sheet and is well-positioned in the market.

Macro & Sentiment
- Macro Headwind Score: 3/10
- Inflation is cooling, which is good for the sector.
- Consumer sentiment is rising.

Quantitative Snapshot
- Revenue: $10B (Up 15% YoY)
- Gross Margin: 45% (Expanding)
- P/E Ratio: 25x
- FCF: Positive and growing.

Fundamental Analysis
- Strong competitive moat due to network effects.
- Risks include regulatory changes and new entrants.
- Strategic focus on AI integration.

Technical Analysis
- Current Price: 120.00
- Trend: Bullish
- Key Levels: Support at 110, Resistance at 130.
- RSI: 60 (Neutral)

Scenario Analysis
- Base Case: $140 (60% prob)
- Bull Case: $160 (20% prob)
- Bear Case: $90 (20% prob)
- Expected Return: +15%

Actionable Takeaways
- Enter at current levels.
- Size position at 2% of portfolio.
- Watch for next earnings report.

Data Caveats
- Some international segment data was estimated.
""",
        "details": {
            "Macro & Sentiment Analyst": f"Detailed macro analysis for {ticker}...",
            "Quantitative Analyst": f"Detailed quant data for {ticker}...",
            "Technical Analyst": f"Detailed charts for {ticker}...",
            "Fundamental Strategist": f"Detailed strategy for {ticker}...",
            "Chief Investment Officer": f"Final synthesized report for {ticker}..."
        },
        "revision_history": []
    }
