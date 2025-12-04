import sys
from src.crew import run_analysis

def main():
    print("### Welcome to the AI Investment Firm ###")
    
    if len(sys.argv) > 1:
        ticker_input = sys.argv[1].strip().upper()
    else:
        ticker_input = input("Enter the stock ticker (e.g., TSLA): ").strip().upper()
    
    if not ticker_input:
        print("Defaulting to TSLA")
        ticker_input = "TSLA"

    try:
        result = run_analysis(ticker_input)
        print("\n\n########################")
        print("## FINAL INVESTMENT MEMO ##")
        print("########################\n")
        print(result)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()

