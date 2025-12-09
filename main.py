import sys
import json
from datetime import datetime
from src.managed_crew import run_managed_analysis

def main():
    print("### Welcome to the AI Investment Firm (Managed Mode) ###")

    if len(sys.argv) > 1:
        ticker_input = sys.argv[1].strip().upper()
    else:
        ticker_input = input("Enter the stock ticker (e.g., TSLA): ").strip().upper()

    if not ticker_input:
        print("Defaulting to TSLA")
        ticker_input = "TSLA"

    try:
        result = run_managed_analysis(ticker_input)

        # Print to console
        print("\n\n########################")
        print("## FINAL INVESTMENT MEMO ##")
        print("########################\n")
        print(result["final_report"])

        # Write full output to file for analysis
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"output_{ticker_input}_{timestamp}.txt"

        with open(output_file, "w") as f:
            f.write(f"EQUITY ANALYSIS: {ticker_input}\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write("=" * 80 + "\n\n")

            f.write("FINAL INVESTMENT MEMO\n")
            f.write("-" * 40 + "\n")
            f.write(result["final_report"])
            f.write("\n\n")

            f.write("=" * 80 + "\n")
            f.write("INDIVIDUAL AGENT OUTPUTS\n")
            f.write("=" * 80 + "\n\n")

            for agent, output in result["details"].items():
                f.write(f"\n{'=' * 40}\n")
                f.write(f"{agent}\n")
                f.write(f"{'=' * 40}\n")
                f.write(output if output else "No output")
                f.write("\n")

            f.write("\n\n")
            f.write("=" * 80 + "\n")
            f.write("REVISION HISTORY (Manager Critiques)\n")
            f.write("=" * 80 + "\n\n")

            for agent_history in result["revision_history"]:
                f.write(f"\n--- {agent_history['agent']} ---\n")
                f.write(f"Total Iterations: {agent_history['total_iterations']}\n")
                f.write(f"Final Approved: {agent_history['final_approved']}\n\n")

                for iteration in agent_history["history"]:
                    f.write(f"  Iteration {iteration['iteration']}:\n")
                    f.write(f"    Approved: {iteration['approved']}\n")
                    if iteration["critique"]:
                        f.write(f"    Critique: {iteration['critique']}\n")
                    if iteration["revision_instructions"]:
                        f.write(f"    Instructions: {iteration['revision_instructions']}\n")
                    f.write("\n")

        print(f"\n✅ Full output saved to: {output_file}")

    except Exception as e:
        print(f"An error occurred: {e}")
        raise

if __name__ == "__main__":
    main()

