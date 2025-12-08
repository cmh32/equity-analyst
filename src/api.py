from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.crew import run_analysis
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
        # run_analysis returns a CrewOutput object
        crew_output = run_analysis(ticker)
        
        # Extract individual task outputs
        details = {}
        if hasattr(crew_output, 'tasks_output'):
            for task_out in crew_output.tasks_output:
                # Use the agent's role as the key, or fall back to description/summary
                key = task_out.agent if task_out.agent else "Unknown Agent"
                details[key] = task_out.raw

        return {
            "ticker": ticker,
            "final_report": crew_output.raw,
            "details": details
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
