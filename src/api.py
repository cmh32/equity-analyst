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
            for i, task_out in enumerate(crew_output.tasks_output):
                # 1. Try to get the agent name directly
                agent_name = None
                if hasattr(task_out, 'agent') and task_out.agent:
                    agent_name = str(task_out.agent)
                
                # 2. Fallback: Infer agent from task description
                if not agent_name:
                    desc = getattr(task_out, 'description', "").lower()
                    if "macro" in desc:
                        agent_name = "Macro & Sentiment Analyst"
                    elif "financial metrics" in desc or "revenue cagr" in desc:
                        agent_name = "Quantitative Analyst"
                    elif "strategic analysis" in desc or "risk factors" in desc:
                        agent_name = "Fundamental Strategist"
                    elif "technical analysis" in desc:
                        agent_name = "Technical Analyst"
                    elif "synthesize" in desc or "investment memo" in desc:
                        agent_name = "Chief Investment Officer"
                    else:
                        agent_name = f"Agent {i+1}"

                # 3. Handle Duplicate Keys (e.g. if multiple tasks map to same agent)
                key = agent_name
                counter = 1
                while key in details:
                    key = f"{agent_name} ({counter})"
                    counter += 1

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
