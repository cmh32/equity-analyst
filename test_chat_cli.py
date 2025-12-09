import requests
import sys

BASE_URL = "http://localhost:8000"

def main():
    print("### Quick Chat Tester ###")
    print("This tool connects to your running API to test the chat functionality.")
    print("Make sure you have seeded data (e.g., via /debug/seed/TEST) or run an analysis first.\n")

    ticker = input("Enter ticker to chat about (default: TEST): ").strip().upper()
    if not ticker:
        ticker = "TEST"

    # Optional: Try to seed if it's TEST and not found? 
    # For now, let's just assume it's there or user knows what they are doing.
    # actually, let's try to 'ping' it first.
    
    print(f"\nConnecting to chat for {ticker}...")

    history = []
    
    while True:
        try:
            question = input("\nYou: ").strip()
        except EOFError:
            break
            
        if not question or question.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break

        payload = {
            "ticker": ticker,
            "question": question,
            "history": history[-6:] # Keep last 6 messages
        }

        try:
            response = requests.post(f"{BASE_URL}/chat", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get("response", "No response received.")
                print(f"AI: {answer}")
                
                # Update history
                history.append({"role": "user", "content": question})
                history.append({"role": "assistant", "content": answer})
                
            elif response.status_code == 404:
                print(f"Error: No analysis found for {ticker}.")
                print("Tip: Run 'curl -X POST http://localhost:8000/debug/seed/TEST' to seed mock data.")
                break
            else:
                print(f"Error {response.status_code}: {response.text}")

        except requests.exceptions.ConnectionError:
            print("Error: Could not connect to localhost:8000. Is the server running?")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            break

if __name__ == "__main__":
    main()
