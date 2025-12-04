import json
import requests
import yfinance as yf
from crewai.tools import BaseTool
from crewai_tools import MDXSearchTool
from .config import get_api_key

class BrowsingTool(BaseTool):
    name: str = "Search the internet"
    description: str = "Useful for searching news. Input should be a search query string."

    def _run(self, query: str) -> str:
        # 🛡️ Handle Dictionary Inputs (Common CrewAI Hallucination)
        if isinstance(query, dict):
            query = query.get('query') or query.get('q') or str(query)

        serper_api_key = get_api_key("SERPER_API_KEY")
        if not serper_api_key:
            return "Error: SERPER_API_KEY not set."

        url = "https://google.serper.dev/search"
        payload = json.dumps({"q": str(query), "num": 5})
        headers = {'X-API-KEY': serper_api_key, 'Content-Type': 'application/json'}
        try:
            response = requests.post(url, headers=headers, data=payload)
            return response.text if response.status_code == 200 else f"Error: {response.text}"
        except Exception as e:
            return f"Error: {str(e)}"

class TechnicalAnalysisTool(BaseTool):
    name: str = "Get Technical Indicators"
    description: str = "Calculates technical indicators (RSI, SMA, Support/Resistance) for a given ticker."

    def _run(self, ticker: str) -> str:
        try:
            if isinstance(ticker, dict):
                ticker = ticker.get('ticker') or list(ticker.values())[0]
            ticker = str(ticker).strip().upper()

            stock = yf.Ticker(ticker)
            hist = stock.history(period="6mo")

            if hist.empty:
                return f"No price data found for {ticker}."

            current_price = hist['Close'].iloc[-1]

            # Simple Moving Average (50 day)
            sma_50 = hist['Close'].rolling(window=50).mean().iloc[-1]

            # Bollinger Bands (20-day SMA +/- 2 std dev)
            sma_20 = hist['Close'].rolling(window=20).mean().iloc[-1]
            std_20 = hist['Close'].rolling(window=20).std().iloc[-1]

            support_level = sma_20 - (2 * std_20)
            resistance_level = sma_20 + (2 * std_20)  # <--- ADDED THIS LINE

            # RSI Calculation (14-day)
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1]

            trend = "Bullish" if current_price > sma_50 else "Bearish"

            report = {
                "Ticker": ticker,
                "Current_Price": round(current_price, 2),
                "Trend_Signal": trend,
                "SMA_50_Day": round(sma_50, 2),
                "RSI_14_Day": round(rsi, 2),
                "Support_Level_Bollinger": round(support_level, 2), # Renamed key for clarity
                "Resistance_Level_Bollinger": round(resistance_level, 2), # Renamed key for clarity
                "Analysis_Note": "Trend based on Price vs 50-Day SMA. Support/Resistance are Bollinger Bands."
            }

            return json.dumps(report, indent=2)

        except Exception as e:
            return f"Error calculating technicals: {e}"

class YFinanceFundamentalsTool(BaseTool):
    name: str = "Get Financial Metrics"
    description: str = "Fetches calculated financial ratios and key metrics for a stock. Input is ticker (e.g. 'INTC')."

    def _run(self, ticker: str) -> str:
        try:
            if isinstance(ticker, dict):
                ticker = ticker.get('ticker') or list(ticker.values())[0]
            ticker = str(ticker).strip().upper()

            stock = yf.Ticker(ticker)
            info = stock.info

            # 1. Safe Extraction Helper
            def get_metric(key, default="N/A"):
                val = info.get(key)
                if val is None:
                    return default
                return val

            # 2. Extract Data
            # We use Yahoo's calculated fields to ensure the Quant agent gets clean data.
            data = {
                "Ticker": ticker,
                "Current_Price": get_metric("currentPrice"),
                "Market_Cap": get_metric("marketCap"),
                "Trailing_PE": get_metric("trailingPE"),
                "Forward_PE": get_metric("forwardPE"),
                "Price_to_Book": get_metric("priceToBook"),
                "Profit_Margins": get_metric("profitMargins"),
                "Gross_Margins": get_metric("grossMargins"),
                "Operating_Margins": get_metric("operatingMargins"),
                "Return_on_Equity": get_metric("returnOnEquity"),
                "Revenue_Growth": get_metric("revenueGrowth"),
                "Total_Debt": get_metric("totalDebt"),
                "Total_Cash": get_metric("totalCash"),
                "Debt_to_Equity": get_metric("debtToEquity"),
                "Free_Cash_Flow": get_metric("freeCashflow")
            }

            return json.dumps(data, indent=2)

        except Exception as e:
            return f"Error fetching fundamentals: {e}"

class HistoricalFinancialsTool(BaseTool):
    name: str = "Get Historical Financials"
    description: str = "Fetches historical financial statements (Income Statement, Balance Sheet, Cash Flow) for the last 4 years to analyze trends."

    def _run(self, ticker: str) -> str:
        try:
            if isinstance(ticker, dict):
                ticker = ticker.get('ticker') or list(ticker.values())[0]
            ticker = str(ticker).strip().upper()

            stock = yf.Ticker(ticker)

            # 1. Fetch the Dataframes
            # financials = Income Statement, balance_sheet = Balance Sheet, cashflow = Cash Flow
            income_stmt = stock.financials
            balance_sheet = stock.balance_sheet
            cash_flow = stock.cashflow

            if income_stmt.empty:
                return f"No historical financials found for {ticker}."

            # 2. Define Key Metrics to Extract (To save tokens, don't grab everything)
            # You can add more rows here based on what your Quant needs
            key_metrics = [
                "Total Revenue",
                "Net Income",
                "Operating Income",
                "Gross Profit",
                "Basic EPS"
            ]

            bs_metrics = [
                "Total Assets",
                "Total Liabilities Net Minority Interest",
                "Stockholders Equity"
            ]

            cf_metrics = [
                "Free Cash Flow",
                "Operating Cash Flow",
                "Capital Expenditure"
            ]

            # 3. Extraction Helper
            def extract_to_md(df, metrics_list, title):
                available_metrics = [m for m in metrics_list if m in df.index]
                if not available_metrics:
                    return ""

                # Slice the dataframe, take last 4 columns (years), and divide by 1B or 1M for readability if needed
                # Here we just keep raw numbers or convert to string
                subset = df.loc[available_metrics].iloc[:, :4] # Last 4 periods

                # Clean column names (Dates) to simple strings
                subset.columns = [c.strftime('%Y-%m-%d') for c in subset.columns]

                return f"### {title}\n" + subset.to_markdown() + "\n\n"

            # 4. Construct Report
            report = f"## Historical Financial Trends for {ticker}\n"
            report += extract_to_md(income_stmt, key_metrics, "Income Statement")
            report += extract_to_md(balance_sheet, bs_metrics, "Balance Sheet")
            report += extract_to_md(cash_flow, cf_metrics, "Cash Flow")

            return report

        except Exception as e:
            return f"Error fetching historical financials: {e}"

class HistoricalPriceActionTool(BaseTool):
    name: str = "Get Price History"
    description: str = "Fetches monthly historical price summaries for the last year to identify long-term trends."

    def _run(self, ticker: str) -> str:
        try:
            if isinstance(ticker, dict):
                ticker = ticker.get('ticker') or list(ticker.values())[0]
            ticker = str(ticker).strip().upper()

            stock = yf.Ticker(ticker)

            # Get 1 year of data
            hist = stock.history(period="1y")

            if hist.empty:
                return f"No price history found for {ticker}."

            # Resample to Monthly to save tokens (End of Month)
            # We get the last price of the month, and the Max High / Min Low of that month
            monthly_df = hist['Close'].resample('ME').last().to_frame(name="Close")
            monthly_df['High'] = hist['High'].resample('ME').max()
            monthly_df['Low'] = hist['Low'].resample('ME').min()
            monthly_df['Volume'] = hist['Volume'].resample('ME').sum()

            # Calculate Monthly Return
            monthly_df['MoM % Change'] = monthly_df['Close'].pct_change() * 100

            # Formatting
            monthly_df.index = monthly_df.index.strftime('%Y-%m')
            monthly_df = monthly_df.round(2)

            # Reverse to show most recent first
            monthly_df = monthly_df.sort_index(ascending=False)

            return f"## Monthly Price Action (1 Year) for {ticker}\n" + monthly_df.to_markdown()

        except Exception as e:
            return f"Error fetching price history: {e}"


class CustomMDXTool(BaseTool):
    name: str = "Search 10-K Content"
    description: str = "Search the 10-K report. Useful for risk factors, management discussion, and qualitative analysis. Input must be a specific search query string."
    mdx_tool: object = None

    # FIX: Use **kwargs so it accepts 'mdx' and 'config' from your main block
    def __init__(self, **kwargs):
        super().__init__()

        # We extract the specific args we need to initialize the internal tool
        mdx_path = kwargs.get('mdx')
        config = kwargs.get('config')

        # Initialize the actual heavy-lifting tool inside
        self.mdx_tool = MDXSearchTool(
            mdx=mdx_path,
            config=config
        )

    def _run(self, query: str) -> str:
        # 1. Sanitize Input (The Fix)
        cleaned_query = query
        if isinstance(query, dict):
            cleaned_query = query.get('query') or query.get('search_query') or query.get('topic') or str(query)

        # 2. Run the internal tool
        try:
            return self.mdx_tool.run(cleaned_query)
        except Exception as e:
            return f"Error querying document: {str(e)}"
