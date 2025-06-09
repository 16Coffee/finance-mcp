import json
import os
from enum import Enum

import pandas as pd
import requests
from mcp.server.fastmcp import FastMCP


# Define an enum for the type of financial statement
class FinancialType(str, Enum):
    income_stmt_annual = "income_stmt_annual"
    income_stmt_quarterly = "income_stmt_quarterly"
    balance_sheet_annual = "balance_sheet_annual"
    balance_sheet_quarterly = "balance_sheet_quarterly"
    cashflow_annual = "cashflow_annual"
    cashflow_quarterly = "cashflow_quarterly"


# Initialize FastMCP server
fmp_server = FastMCP(
    "financialmodelingprep",
    instructions="""
# Financial Modeling Prep MCP Server

This server retrieves stock market data using Financial Modeling Prep APIs.
Before using these tools, set the `FMP_API_KEY` environment
variable to your Financial Modeling Prep API key.

Available.tools:
- get_historical_stock_prices: Get historical stock prices for a given ticker symbol. Includes Date, Open, High, Low, Close, and Volume.
- get_stock_info: Get company overview and financial metrics for a given ticker symbol.
- get_news_sentiment: Get recent news articles for a given ticker symbol.
- get_stock_actions: Get dividends and stock split history for a given ticker symbol.
- get_financial_statement: Get financial statements for a given ticker symbol. Supported types: income_stmt_annual, income_stmt_quarterly, balance_sheet_annual, balance_sheet_quarterly, cashflow_annual, cashflow_quarterly.
- get_option_expiration_dates: Fetch available option expiration dates for a given ticker symbol.
- get_option_chain: Fetch the option chain for a given ticker symbol, expiration date, and option type.
""",
)


@fmp_server.tool(
    name="get_historical_stock_prices",
    description="""Get historical stock prices for a given ticker symbol using Financial Modeling Prep. Includes Date, Open, High, Low, Close and Volume.
Args:
    ticker: str
        The ticker symbol of the stock to get historical prices for, e.g. "AAPL"
    period : str
        Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
        Either Use period parameter or use start and end
        Default is "1mo"
    interval : str
        Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
        Intraday data cannot extend last 60 days
        Default is "1d"
""",
)
async def get_historical_stock_prices(
    ticker: str, period: str = "1mo", interval: str = "1d"
) -> str:
    """Get historical stock prices for a given ticker symbol"""

    api_key = os.environ.get("FMP_API_KEY")
    if not api_key:
        return "Error: FMP_API_KEY environment variable not set."

    base = "https://financialmodelingprep.com/api/v3"
    try:
        if interval in ["1min", "5min", "15min", "30min", "1hour", "4hour"]:
            url = f"{base}/historical-chart/{interval}/{ticker}"
            resp = requests.get(url, params={"apikey": api_key}, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        else:
            url = f"{base}/historical-price-full/{ticker}"
            resp = requests.get(url, params={"apikey": api_key}, timeout=10)
            resp.raise_for_status()
            data = resp.json().get("historical", [])
    except Exception as e:
        return f"Error: getting historical stock prices for {ticker}: {e}"

    df = pd.DataFrame(data)
    if not df.empty:
        if "date" in df.columns:
            df.rename(columns={"date": "Date"}, inplace=True)
        df = df[["Date", "open", "high", "low", "close", "volume"]]
        df.columns = [c.title() for c in df.columns]

    period_map = {
        "1d": pd.Timedelta(days=1),
        "5d": pd.Timedelta(days=5),
        "1mo": pd.Timedelta(days=30),
        "3mo": pd.Timedelta(days=90),
        "6mo": pd.Timedelta(days=180),
        "1y": pd.Timedelta(days=365),
        "2y": pd.Timedelta(days=730),
        "5y": pd.Timedelta(days=1825),
        "10y": pd.Timedelta(days=3650),
    }

    if period == "ytd":
        start = pd.Timestamp.now().replace(month=1, day=1)
    elif period != "max" and period in period_map:
        start = pd.Timestamp.now() - period_map[period]
    else:
        start = None

    if start is not None and not df.empty:
        df = df[df["Date"] >= start]

    return df.to_json(orient="records", date_format="iso")


@fmp_server.tool(
    name="get_stock_info",
    description="""Get company overview and key metrics for a given ticker symbol using Financial Modeling Prep.

Args:
    ticker: str
        The ticker symbol of the stock to get information for, e.g. "AAPL"
""",
)
async def get_stock_info(ticker: str) -> str:
    """Get stock information for a given ticker symbol"""
    api_key = os.environ.get("FMP_API_KEY")
    if not api_key:
        return "Error: FMP_API_KEY environment variable not set."

    url = f"https://financialmodelingprep.com/api/v3/profile/{ticker}"
    try:
        resp = requests.get(url, params={"apikey": api_key}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return f"Error: getting stock information for {ticker}: {e}"
    return json.dumps(data[0] if isinstance(data, list) and data else data)


@fmp_server.tool(
    name="get_news_sentiment",
    description="""Get news for a given ticker symbol using Financial Modeling Prep.

Args:
    ticker: str
        The ticker symbol of the stock to get news for, e.g. "AAPL"
""",
)
async def get_news_sentiment(ticker: str) -> str:
    """Get news for a given ticker symbol"""

    api_key = os.environ.get("FMP_API_KEY")
    if not api_key:
        return "Error: FMP_API_KEY environment variable not set."

    url = "https://financialmodelingprep.com/api/v4/general_news"
    try:
        resp = requests.get(
            url, params={"tickers": ticker, "page": 0, "size": 50, "apikey": api_key}, timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return f"Error: getting news for {ticker}: {e}"

    news_list = []
    for item in data:
        title = item.get("title", "")
        summary = item.get("text", "")
        link = item.get("url", "")
        news_list.append(f"Title: {title}\nSummary: {summary}\nURL: {link}")

    if not news_list:
        return f"No news found for {ticker}"

    return "\n\n".join(news_list)


@fmp_server.tool(
    name="get_stock_actions",
    description="""Get stock dividends and stock splits for a given ticker symbol using Financial Modeling Prep.

Args:
    ticker: str
        The ticker symbol of the stock to get stock actions for, e.g. "AAPL"
""",
)
async def get_stock_actions(ticker: str) -> str:
    """Get stock dividends and stock splits for a given ticker symbol"""
    api_key = os.environ.get("FMP_API_KEY")
    if not api_key:
        return "Error: FMP_API_KEY environment variable not set."

    base = "https://financialmodelingprep.com/api/v3"
    try:
        div_resp = requests.get(
            f"{base}/historical-price-full/stock_dividend/{ticker}",
            params={"apikey": api_key},
            timeout=10,
        )
        div_resp.raise_for_status()
        div_df = pd.DataFrame(div_resp.json().get("historical", []))
        split_resp = requests.get(
            f"{base}/historical-price-full/stock_split/{ticker}",
            params={"apikey": api_key},
            timeout=10,
        )
        split_resp.raise_for_status()
        split_df = pd.DataFrame(split_resp.json().get("historical", []))
    except Exception as e:
        return f"Error: getting stock actions for {ticker}: {e}"

    return json.dumps(
        {
            "dividends": div_df.to_dict("records"),
            "splits": split_df.to_dict("records"),
        }
    )


@fmp_server.tool(
    name="get_financial_statement",
    description="""Get financial statement for a given ticker symbol using Financial Modeling Prep. Supported types: income_stmt_annual, income_stmt_quarterly, balance_sheet_annual, balance_sheet_quarterly, cashflow_annual, cashflow_quarterly.

Args:
    ticker: str
        The ticker symbol of the stock to get financial statement for, e.g. "AAPL"
    financial_type: str
        The type of financial statement to get. Use one of: income_stmt_annual, income_stmt_quarterly, balance_sheet_annual, balance_sheet_quarterly, cashflow_annual, cashflow_quarterly.
""",
)
async def get_financial_statement(ticker: str, financial_type: str) -> str:
    """Get financial statement for a given ticker symbol"""

    api_key = os.environ.get("FMP_API_KEY")
    if not api_key:
        return "Error: FMP_API_KEY environment variable not set."

    base = "https://financialmodelingprep.com/api/v3"
    period = "annual"
    if financial_type in [
        FinancialType.income_stmt_quarterly,
        FinancialType.balance_sheet_quarterly,
        FinancialType.cashflow_quarterly,
    ]:
        period = "quarter"

    endpoint_map = {
        FinancialType.income_stmt_annual: "income-statement",
        FinancialType.income_stmt_quarterly: "income-statement",
        FinancialType.balance_sheet_annual: "balance-sheet-statement",
        FinancialType.balance_sheet_quarterly: "balance-sheet-statement",
        FinancialType.cashflow_annual: "cash-flow-statement",
        FinancialType.cashflow_quarterly: "cash-flow-statement",
    }
    endpoint = endpoint_map.get(FinancialType(financial_type))
    if not endpoint:
        return "Error: invalid financial type"
    url = f"{base}/{endpoint}/{ticker}"
    try:
        resp = requests.get(url, params={"period": period, "apikey": api_key}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return f"Error: getting financial statement for {ticker}: {e}"

    return json.dumps(data)


@fmp_server.tool(
    name="get_option_expiration_dates",
    description="""Fetch the available options expiration dates for a given ticker symbol using Financial Modeling Prep.

Args:
    ticker: str
        The ticker symbol of the stock to get option expiration dates for, e.g. "AAPL"
""",
)
async def get_option_expiration_dates(ticker: str) -> str:
    """Fetch the available options expiration dates for a given ticker symbol."""

    api_key = os.environ.get("FMP_API_KEY")
    if not api_key:
        return "Error: FMP_API_KEY environment variable not set."

    base = "https://financialmodelingprep.com/api/v3"
    try:
        resp = requests.get(
            f"{base}/options/available-expirations/{ticker}", params={"apikey": api_key}, timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return f"Error: getting option expiration dates for {ticker}: {e}"
    expirations = data if isinstance(data, list) else data.get("expirations", [])
    return json.dumps(sorted(expirations))


@fmp_server.tool(
    name="get_option_chain",
    description="""Fetch the option chain for a given ticker symbol, expiration date, and option type using Financial Modeling Prep.

Args:
    ticker: str
        The ticker symbol of the stock to get option chain for, e.g. "AAPL"
    expiration_date: str
        The expiration date for the options chain (format: 'YYYY-MM-DD')
    option_type: str
        The type of option to fetch ('calls' or 'puts')
""",
)
async def get_option_chain(ticker: str, expiration_date: str, option_type: str) -> str:
    """Fetch the option chain for a given ticker symbol, expiration date, and option type."""

    api_key = os.environ.get("FMP_API_KEY")
    if not api_key:
        return "Error: FMP_API_KEY environment variable not set."

    base = "https://financialmodelingprep.com/api/v3"
    try:
        resp = requests.get(
            f"{base}/options/chain/{ticker}",
            params={"expiration": expiration_date, "apikey": api_key},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return f"Error: getting option chain for {ticker}: {e}"

    filtered = [
        item
        for item in data
        if item.get("expirationDate") == expiration_date
        and item.get("optionType", "").lower() == option_type.lower()
    ]
    return json.dumps(filtered)


if __name__ == "__main__":
    # Initialize and run the server
    print("Starting Financial Modeling Prep MCP server...")
    fmp_server.run(transport="stdio")
