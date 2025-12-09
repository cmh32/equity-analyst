"""
Manager Agent for multi-agent equity analysis system.
Orchestrates specialist agents and manages revision cycles.
"""
import json
from openai import OpenAI
from .config import get_api_key

# Manager uses gpt-5-nano for fast evaluation (checklist task, not creative)
MANAGER_MODEL = "gpt-5-nano"

# Initialize OpenAI client
client = OpenAI(api_key=get_api_key("OPENAI_API_KEY"))

# Manager's system prompt for critiquing financial analysis
MANAGER_SYSTEM_PROMPT = """You are a Senior Investment Research Manager at a top-tier hedge fund.
Your role is to review analyst work for quality, completeness, and accuracy before it reaches the CIO.

When reviewing analyst outputs, evaluate against these criteria:

**For Macro Analysis:**
- Does it address company-specific macro risks (not generic industry commentary)?
- Are all PESTLE categories covered with concrete examples?
- Is the Macro Headwind Score justified with evidence?
- Are tariff/trade, interest rate, and regulatory risks addressed?

**For Quantitative Analysis:**
- Are all key metrics present (P/E, margins, FCF, revenue growth)?
- Is historical data included (3+ years of trends)?
- Are calculations shown (CAGR, margin expansion/contraction)?
- Is missing data clearly flagged as "Data Unavailable"?

**For Fundamental/Strategic Analysis:**
- Are 10-K risk factors specifically cited?
- Is there a link between financial metrics and qualitative risks?
- Is competitive positioning discussed?
- Are moat/competitive advantages identified?

**For Technical Analysis:**
- Are support/resistance levels provided?
- Is RSI interpretation included?
- Is the 1-year trend context given?
- Are key levels (52-week high/low) mentioned?

**For CIO Investment Memo:**
- Is there a clear Buy/Sell/Hold recommendation?
- Is Conviction Score (0-10) provided with justification?
- Is Kill Switch Price specified (with methodology noted)?
- Does the executive summary capture the key thesis in 2-3 sentences?
- Are all four analyst inputs (Macro, Quant, Fundamental, Technical) synthesized?
- Is the reasoning logically coherent (do the bullet points support the recommendation)?
- Are any data gaps or caveats clearly acknowledged?
- Is the memo actionable for a portfolio manager?

Your critique must be ACTIONABLE. Instead of "needs more detail", say exactly what's missing:
- BAD: "The macro analysis needs more depth"
- GOOD: "Missing: tariff risk analysis for China exposure, interest rate sensitivity for debt load"

Output Format:
{
    "approved": true/false,
    "critique": "Specific issues found (if not approved)",
    "revision_instructions": "Exactly what the agent should add/fix (if not approved)"
}
"""


def critique_agent_output(agent_role: str, agent_output: str, company_name: str, ticker: str) -> dict:
    """
    Manager reviews a single agent's output and provides critique.

    Args:
        agent_role: The role of the agent being reviewed (e.g., "Macro & Sentiment Analyst")
        agent_output: The text output from the agent
        company_name: The company being analyzed
        ticker: Stock ticker symbol

    Returns:
        dict with keys: approved (bool), critique (str), revision_instructions (str)
    """
    review_prompt = f"""Review this {agent_role} output for {company_name} ({ticker}):

--- AGENT OUTPUT ---
{agent_output}
--- END OUTPUT ---

Evaluate against quality standards for {agent_role} work.
Be strict but fair. Only approve if the analysis meets professional standards.

Return your evaluation as JSON:
{{"approved": true/false, "critique": "...", "revision_instructions": "..."}}
"""

    response = client.chat.completions.create(
        model=MANAGER_MODEL,
        messages=[
            {"role": "system", "content": MANAGER_SYSTEM_PROMPT},
            {"role": "user", "content": review_prompt}
        ],
        response_format={"type": "json_object"}
    )

    result = json.loads(response.choices[0].message.content)

    # Ensure all expected keys exist
    return {
        "approved": result.get("approved", False),
        "critique": result.get("critique", ""),
        "revision_instructions": result.get("revision_instructions", "")
    }


def build_revision_prompt(original_task_description: str, revision_instructions: str,
                          previous_output: str, iteration: int) -> str:
    """
    Build a revised task description that includes manager feedback.

    Args:
        original_task_description: The original task instructions
        revision_instructions: Manager's specific revision requirements
        previous_output: The agent's previous attempt
        iteration: Current revision number (1, 2, or 3)

    Returns:
        Updated task description with revision context
    """
    return f"""
{original_task_description}

---
**REVISION {iteration} REQUIRED**

Your previous output was reviewed by the Research Manager. Here is your previous work:

--- PREVIOUS OUTPUT ---
{previous_output}
--- END PREVIOUS OUTPUT ---

**Manager's Revision Instructions:**
{revision_instructions}

IMPORTANT: Address ALL points in the revision instructions. Build upon your previous work -
do not start from scratch. Keep what was good and fix what was flagged.
---
"""


class RevisionHistory:
    """Tracks the critique/revision history for an agent."""

    def __init__(self, agent_role: str):
        self.agent_role = agent_role
        self.iterations = []

    def add_iteration(self, output: str, critique: dict, iteration_num: int):
        """Record a revision iteration."""
        self.iterations.append({
            "iteration": iteration_num,
            "output_preview": output[:500] + "..." if len(output) > 500 else output,
            "approved": critique["approved"],
            "critique": critique["critique"],
            "revision_instructions": critique["revision_instructions"]
        })

    def to_dict(self) -> dict:
        """Export history for API response."""
        return {
            "agent": self.agent_role,
            "total_iterations": len(self.iterations),
            "final_approved": self.iterations[-1]["approved"] if self.iterations else False,
            "history": self.iterations
        }

    def summary(self) -> str:
        """Human-readable summary of revisions."""
        if not self.iterations:
            return f"{self.agent_role}: No revisions recorded"

        lines = [f"**{self.agent_role}** - {len(self.iterations)} iteration(s)"]
        for it in self.iterations:
            status = "✅ Approved" if it["approved"] else "🔄 Revision needed"
            lines.append(f"  Round {it['iteration']}: {status}")
            if it["critique"] and not it["approved"]:
                lines.append(f"    Feedback: {it['critique'][:100]}...")
        return "\n".join(lines)
