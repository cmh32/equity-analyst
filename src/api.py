from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from src.managed_crew import run_managed_analysis
from src.chat_service import chat_service
from src.mock_data import get_mock_analysis
import uvicorn
import os

app = FastAPI(title="Equity Analyst API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, allow all. Restrict in production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalysisRequest(BaseModel):
    ticker: str


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    ticker: str
    question: str
    history: Optional[List[ChatMessage]] = None

@app.get("/")
def read_root():
    return {"message": "Welcome to the Equity Analyst API. Use /analyze/{ticker} to start."}

@app.post("/debug/seed/{ticker}")
def seed_mock_data(ticker: str):
    """
    Seeds the chat service with mock data for troubleshooting.
    """
    ticker = ticker.strip().upper()
    try:
        mock_data = get_mock_analysis(ticker)
        chat_service.index_analysis(ticker, mock_data)
        return {"message": f"Successfully seeded mock data for {ticker}", "data": mock_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze")
def analyze_stock(request: AnalysisRequest):
    ticker = request.ticker.strip().upper()
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker symbol is required")

    try:
        result = run_managed_analysis(ticker)

        # Index the analysis for RAG chat
        chat_service.index_analysis(ticker, result)

        return {
            "ticker": result["ticker"],
            "final_report": result["final_report"],
            "details": result["details"],
            "revision_history": result["revision_history"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat")
def chat_with_analysis(request: ChatRequest):
    """
    Chat with the analysis using RAG retrieval.
    """
    ticker = request.ticker.strip().upper()

    if not chat_service.has_analysis(ticker):
        raise HTTPException(
            status_code=404,
            detail=f"No analysis found for {ticker}. Please run an analysis first."
        )

    try:
        # Convert history to dict format
        history = None
        if request.history:
            history = [{"role": m.role, "content": m.content} for m in request.history]

        response = chat_service.chat(ticker, request.question, history)
        return {"response": response, "ticker": ticker}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
