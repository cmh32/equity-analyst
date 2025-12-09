from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.managed_crew import run_managed_analysis
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

@app.get("/")
def read_root():
    return {"message": "Welcome to the Equity Analyst API. Use /analyze/{ticker} to start."}

@app.post("/analyze")
def analyze_stock(request: AnalysisRequest):
    ticker = request.ticker.strip().upper()
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker symbol is required")

    try:
        result = run_managed_analysis(ticker)
        return {
            "ticker": result["ticker"],
            "final_report": result["final_report"],
            "details": result["details"],
            "revision_history": result["revision_history"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
