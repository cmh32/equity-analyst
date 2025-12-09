import sys
from src.mock_data import get_mock_analysis
from src.chat_service import chat_service

def main():
    ticker = "TEST_MOCK"
    print(f"--- 🚀 Initializing Chatbot with Mock Data ({ticker}) ---")
    
    # 1. Load the mock data (Simulates the output of the 20-min analysis)
    print("1. Loading mock analysis data...")
    mock_data = get_mock_analysis(ticker)
    
    # 2. Index it using the REAL chat service (Tests the actual ChromaDB + OpenAI logic)
    print("2. Indexing data into Vector Database...")
    try:
        chat_service.index_analysis(ticker, mock_data)
        print("✅ Indexing successful.")
    except Exception as e:
        print(f"❌ Error during indexing: {e}")
        return

    # 3. Start the Chat Loop
    print("\n" + "=" * 60)
    print(f"💬 CHAT TEST MODE - {ticker}")
    print("   This is interacting with the ACTUAL chat_service.py logic.")
    print("   Type 'quit', 'exit', or 'q' to stop.")
    print("=" * 60 + "\n")

    history = []
    
    while True:
        try:
            question = input("\nYou: ").strip()
        except EOFError:
            break

        if not question:
            continue
            
        if question.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break

        try:
            # Call the real chat method
            response = chat_service.chat(ticker, question, history)
            
            print(f"\nAI: {response}")
            
            # Maintain simple history for context
            history.append({"role": "user", "content": question})
            history.append({"role": "assistant", "content": response})
            
        except Exception as e:
            print(f"\n❌ Error generating response: {e}")

if __name__ == "__main__":
    main()
