import os
import sys

# Add the parent directory of src to the Python path
# Assuming this script is run from the project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from src.chat_service import AnalysisChatService
from src.config import get_api_key, MODEL_NAME

def run_isolated_chat_service_test():
    """
    Runs an isolated test of the AnalysisChatService.
    """
    print("--- Running isolated AnalysisChatService test ---")

    # Ensure OPENAI_API_KEY is set
    # IMPORTANT: Replace "YOUR_OPENAI_API_KEY" with your actual key
    # or ensure it's set as an environment variable.
    if os.getenv("OPENAI_API_KEY") is None:
        print("OPENAI_API_KEY not found in environment variables.")
        print("Please set it or ensure your .env file is correctly configured.")
        # As a fallback for local testing, you could uncomment and set it here:
        # os.environ["OPENAI_API_KEY"] = "sk-YOUR_ACTUAL_OPENAI_KEY_HERE"

    # Mock analysis data
    mock_analysis_data = {
        "final_report": """
Recommendation
-------------
The CIO Memo recommends a 'Hold' rating for MOCK stock due to mixed signals.
Executive Summary
-----------------
MOCK company has shown stable revenue growth but increased operational costs.
Macro & Sentiment
-----------------
Overall market sentiment is neutral towards the sector.
Quantitative Snapshot
---------------------
P/E ratio is slightly above industry average.
Fundamental Analysis
--------------------
Solid balance sheet, but recent debt increase is a concern.
Technical Analysis
------------------
Stock price is trading within a narrow range, showing no clear trend.
Scenario Analysis
-----------------
Best case: market recovery boosts stock. Worst case: increased competition erodes margins.
Actionable Takeaways
--------------------
Monitor Q3 earnings for operational efficiency improvements.
Data Caveats
------------
Reliance on historical data which might not fully predict future performance.
""",
        "details": {
            "Fundamental Agent": "MOCK's revenue grew 5% YoY, but net income decreased by 2% due to higher COGS.",
            "Quantitative Agent": "The 50-day moving average is flat, indicating consolidation. RSI is at 55.",
            "Macro Agent": "Inflation concerns are easing, which might be a positive for growth stocks like MOCK.",
            "Technical Agent": "Support level at $100, resistance at $110. Volume is average.",
            "CIO Memo": "The Chief Investment Officer believes MOCK has potential but current valuations are fair."
        }
    }

    try:
        service = AnalysisChatService()
        print(f"Service initialized. Using model: {MODEL_NAME}")

        print("\n--- Indexing mock analysis data ---")
        service.index_analysis("MOCK", mock_analysis_data)
        print("Indexing complete.")

        print("\n--- Asking a question ---")
        question = "What is the recommendation for MOCK stock and why?"
        print(f"Question: {question}")

        response = service.chat("MOCK", question)
        print(f"\nAssistant: {response}")

        print("\n--- Testing with history ---")
        question2 = "Can you elaborate on the fundamental analysis?"
        history = [{"role": "user", "content": question}, {"role": "assistant", "content": response}]
        print(f"Question: {question2}")
        response2 = service.chat("MOCK", question2, history)
        print(f"\nAssistant: {response2}")


    except Exception as e:
        print(f"\nAn error occurred: {e}")
        # If the error is related to OpenAI API key, provide a more specific message
        if "AuthenticationError" in str(e) or "invalid_api_key" in str(e):
            print("\nIt seems there's an issue with your OpenAI API key.")
            print("Please ensure OPENAI_API_KEY is correctly set in your environment variables or in your .env file.")
        elif "No such file or directory" in str(e) and "src/config.py" in str(e):
             print("\nCould not find `src/config.py`. Please ensure `sys.path.append` is correct or run from the correct directory.")


    print("\n--- Isolated AnalysisChatService test finished ---")

if __name__ == "__main__":
    run_isolated_chat_service_test()
