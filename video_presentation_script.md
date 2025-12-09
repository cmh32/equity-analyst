# Video Presentation Script: Equity Analyst Agent System
**Time:** ~5-7 Minutes
**Speaker:** Colin Hughes
**Context:** Yale LLM Course Final Project

---

## 0:00 - 1:00 | Introduction & The Problem
**(Visual: Title Slide / Face Camera)**

"Hi, I'm Colin Hughes. For my final project, I built an **Equity Analyst Agent System**.

The problem I wanted to solve is that traditional financial research is incredibly labor-intensive. You have to read 10-Ks, check current stock prices, analyze macro trends, and crunch numbers.

If you ask a standard LLM like ChatGPT to 'Analyze Apple,' it usually gives you a generic summary or, worse, hallucinates financial figures. It lacks rigor.

**(Visual: Split screen showing a generic LLM response vs. Your App's architecture diagram)**

My solution wasn't to build a better chatbot, but to build an **AI Workforce**. I created a **Manager-Agent Architecture**.

Instead of one model doing everything, I have specialized agents—a Macro Economist, a Quant, and a Technical Analyst. But the key innovation here is the **Manager Agent**. This agent doesn't generate content; it *critiques* it. It acts as a quality gatekeeper, sending work back for revision if it doesn't meet professional standards. This ensures the final output is grounded, accurate, and useful."

---

## 1:00 - 3:00 | The Live Demo
**(Visual: Screen recording of the Web Interface)**

"Let me show you how it works. This is the web application running locally.

1.  **Input:** I'll enter a ticker, let's say 'NVDA' for Nvidia.
2.  **Orchestration:** When I hit analyze, look at the logs here. We are spinning up three agents in parallel:
    *   The **Macro Agent** is searching the web for PESTLE factors like 'AI chip export bans.'
    *   The **Quant Agent** is hitting the Yahoo Finance API for real data—no hallucinations allowed here.
    *   The **Technical Agent** is calculating RSI and Moving Averages.

**(Visual: Zoom in on the terminal/log output showing the "Manager Reviewing" step)**

3.  **The Feedback Loop:** This is the cool part. Watch this log line: *'Manager reviewing Macro output...'*
    *   If the Manager thinks the analysis is too generic, it rejects it. You can see here [point to log] it might say 'Revision Needed: Specific tariff risks missing.'
    *   The agent then *fixes* its own work before the human ever sees it.

4.  **Final Output:** Once the Manager approves all specific reports, the **CIO Agent** synthesizes everything into this final Investment Memo. It gives a specific Recommendation, a Conviction Score, and a Kill Switch price.

5.  **RAG Chat:** Finally, down here, I can chat with the report. I can ask, 'Why is the conviction score only a 7?' The system uses RAG to retrieve the specific section from the generated report to answer me."

---

## 3:00 - 5:30 | Code Walkthrough (Under the Hood)
**(Visual: Switch to VS Code / IDE)**

"Now, let's look at the code to see how I implemented this. The stack is Python with FastAPI for the backend and CrewAI for the agents.

**(Visual: Open `src/managed_crew.py`)**

**1. Orchestration (`managed_crew.py`):**
This is the main engine. I'm not just chaining prompts. I'm using a `ThreadPoolExecutor` to run the independent agents (Macro, Quant, Technical) in parallel to save time.

But notice the function `run_agent_with_revisions`. This is where the magic happens. It doesn't just run the agent once. It enters a `while` loop controlled by the Manager.

**(Visual: Open `src/manager_agent.py`)**

**2. The Manager Logic (`manager_agent.py`):**
Here is the Manager's system prompt. It's distinct from the others. It has a rubric for every type of analysis. For example, for the *Fundamental* analysis, it explicitly checks: 'Are 10-K risk factors specifically cited?'

If the check fails, the `critique_agent_output` function returns `approved: False` and specific `revision_instructions`. These instructions are injected back into the worker agent's context for the next attempt. This mimics a real-world analyst-associate workflow.

**(Visual: Open `src/chat_service.py`)**

**3. RAG Implementation (`chat_service.py`):**
For the chat feature, I'm using `ChromaDB`. When an analysis is finished, I chunk the text—separating the CIO memo from the detailed agent reports—and embed them. This allows the user to query the *specific* data generated during the session, rather than general knowledge."

---

## 5:30 - 6:30 | Technical Accomplishment & Conclusion
**(Visual: Slide listing the 5 points below)**

"To wrap up, this project hits five key technical accomplishments from the rubric:

1.  **Sophisticated Agent Workflows:** The Manager-Critique loop goes beyond standard chains to create self-correcting agents.
2.  **Search Augmented Retrieval (RAG):** Used for the interactive Q&A on the report.
3.  **Web Application:** It's a fully hosted FastAPI app, not a notebook.
4.  **Multiple Data Sources:** It combines LLM reasoning with real-time Web Search (Serper), Financial APIs (YFinance), and SEC data.
5.  **Conversational Chat:** Providing an interactive layer on top of the static report.

**Utility:**
This tool reduces hours of preliminary due diligence into minutes, and because of the Manager layer, it provides a level of quality assurance that a standard Chat-bot cannot match.

Thanks for watching."

---
