#!/usr/bin/env python3
"""
Quick test script to debug chat functionality without running full analysis.
"""
from src.chat_service import AnalysisChatService

def main():
    print("### Chat Debug Test ###\n")

    # Create a fresh chat service instance
    chat_service = AnalysisChatService()

    # Mock analysis data (simplified version of real output)
    ticker = "TEST"
    mock_analysis = {
        "final_report": """
Recommendation
- Position: Hold
- Conviction Score: 5 / 10
- Kill Switch Price: 796.30
- Rationale: McKesson displays durable revenue growth and strong free cash flow.

Executive Summary
McKesson is growing top-line revenue at a multi-year pace (3-year CAGR ~10.8%) and generating robust free cash flow (TTM FCF ~$6.1B).

Quantitative Snapshot
- Revenue (TTM): 359.051 billion
- Gross Margin: 3.71%
- Operating Margin: 1.34%
- Net Margin: 0.92%
- Free Cash Flow: 5.23 billion

Technical Analysis
- Current Price: 797.93
- Trend: Bearish
- RSI: 32.85 (near oversold)
- Support: 796.30
- Resistance: 812.90
        """,
        "details": {
            "Macro Analyst": "Macro headwind score: 7/10. Political risks include 340B reforms.",
            "Quant Analyst": "Revenue CAGR 10.78%. Margins declining year over year.",
            "Technical Analyst": "RSI at 32.85 indicates oversold conditions. Price near support."
        }
    }

    # Index the mock data
    print("📚 Indexing mock analysis data...")
    chat_service.index_analysis(ticker, mock_analysis)

    # Test chat
    print("\n" + "=" * 50)
    print("💬 CHAT DEBUG MODE")
    print("   Type 'quit' to exit")
    print("=" * 50 + "\n")

    history = []
    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not question:
            print("(empty input, skipping)")
            continue
        if question.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break

        print(f"\n--- Calling chat service ---")
        history.append({"role": "user", "content": question})
        response = chat_service.chat(ticker, question, history)
        print(f"--- Response received ---\n")
        print(f"AI: {response}\n")
        history.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
