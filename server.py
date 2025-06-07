import json
import os
from enum import Enum

import pandas as pd
from alpha_vantage.alphaintelligence import AlphaIntelligence
from alpha_vantage.fundamentaldata import FundamentalData
from alpha_vantage.options import Options
from alpha_vantage.timeseries import TimeSeries
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
alphavantage_server = FastMCP(
    "alphavantage",
    instructions="""
# Alpha Vantage MCP Server

This server retrieves stock market data using Alpha Vantage APIs.
Before using these tools, set the `ALPHAVANTAGE_API_KEY` environment
variable to your Alpha Vantage API key.

Available.tools:
- get_historical_stock_prices: Get historical stock prices for a given ticker symbol. Includes Date, Open, High, Low, Close, Volume, and Adjusted Close where available.
- get_stock_info: Get company overview and financial metrics for a given ticker symbol.
- get_news_sentiment: Get recent news articles for a given ticker symbol.
- get_stock_actions: Get dividends and stock split history for a given ticker symbol.
- get_financial_statement: Get financial statements for a given ticker symbol. Supported types: income_stmt_annual, income_stmt_quarterly, balance_sheet_annual, balance_sheet_quarterly, cashflow_annual, cashflow_quarterly.
- get_option_expiration_dates: Fetch available option expiration dates for a given ticker symbol.
- get_option_chain: Fetch the option chain for a given ticker symbol, expiration date, and option type.
""",
)


@alphavantage_server.tool(
    name="get_historical_stock_prices",
    description="""Get historical stock prices for a given ticker symbol using Alpha Vantage. Includes Date, Open, High, Low, Close, Volume, and Adjusted Close when available.
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

    api_key = os.environ.get("ALPHAVANTAGE_API_KEY")
    if not api_key:
        return "Error: ALPHAVANTAGE_API_KEY environment variable not set."

    ts = TimeSeries(key=api_key, output_format="pandas")
    try:
        if interval in ["1min", "5min", "15min", "30min", "60min"]:
            data, _ = ts.get_intraday(symbol=ticker, interval=interval, outputsize="full")
        elif interval == "1wk":
            data, _ = ts.get_weekly(symbol=ticker)
        elif interval == "1mo":
            data, _ = ts.get_monthly(symbol=ticker)
        elif interval == "1d":
            data, _ = ts.get_daily(symbol=ticker, outputsize="full")
        else:
            return "Error: invalid interval"
    except Exception as e:
        return f"Error: getting historical stock prices for {ticker}: {e}"

    data = data.rename(columns=lambda c: c.split(". ")[-1].title())
    data = data.reset_index(names="Date")

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

    if start is not None:
        data = data[data["Date"] >= start]

    return data.to_json(orient="records", date_format="iso")


@alphavantage_server.tool(
    name="get_stock_info",
    description="""Get company overview and key metrics for a given ticker symbol using Alpha Vantage.

Args:
    ticker: str
        The ticker symbol of the stock to get information for, e.g. "AAPL"
""",
)
async def get_stock_info(ticker: str) -> str:
    """Get stock information for a given ticker symbol"""
    api_key = os.environ.get("ALPHAVANTAGE_API_KEY")
    if not api_key:
        return "Error: ALPHAVANTAGE_API_KEY environment variable not set."

    fd = FundamentalData(key=api_key)
    try:
        data, _ = fd.get_company_overview(symbol=ticker)
    except Exception as e:
        return f"Error: getting stock information for {ticker}: {e}"
    return json.dumps(data)


@alphavantage_server.tool(
    name="get_news_sentiment",
    description="""Get news for a given ticker symbol using Alpha Vantage.

Args:
    ticker: str
        The ticker symbol of the stock to get news for, e.g. "AAPL"
""",
)
async def get_news_sentiment(ticker: str) -> str:
    """Get news for a given ticker symbol"""

    api_key = os.environ.get("ALPHAVANTAGE_API_KEY")
    if not api_key:
        return "Error: ALPHAVANTAGE_API_KEY environment variable not set."

    ai = AlphaIntelligence(key=api_key)
    try:
        data, _ = ai.get_news_sentiment(tickers=ticker)
    except Exception as e:
        return f"Error: getting news for {ticker}: {e}"

    news_list = []
    for item in data.get("feed", []):
        title = item.get("title", "")
        summary = item.get("summary", "")
        url = item.get("url", "")
        news_list.append(f"Title: {title}\nSummary: {summary}\nURL: {url}")

    if not news_list:
        return f"No news found for {ticker}"

    return "\n\n".join(news_list)


@alphavantage_server.tool(
    name="get_stock_actions",
    description="""Get stock dividends and stock splits for a given ticker symbol using Alpha Vantage.

Args:
    ticker: str
        The ticker symbol of the stock to get stock actions for, e.g. "AAPL"
""",
)
async def get_stock_actions(ticker: str) -> str:
    """Get stock dividends and stock splits for a given ticker symbol"""
    api_key = os.environ.get("ALPHAVANTAGE_API_KEY")
    if not api_key:
        return "Error: ALPHAVANTAGE_API_KEY environment variable not set."

    fd = FundamentalData(key=api_key, output_format="pandas")
    try:
        div_df, _ = fd.get_dividends(symbol=ticker)
        split_df, _ = fd.get_splits(symbol=ticker)
    except Exception as e:
        return f"Error: getting stock actions for {ticker}: {e}"

    div_df = div_df.reset_index(names="date")
    split_df = split_df.reset_index(names="date")
    return json.dumps(
        {"dividends": div_df.to_dict("records"), "splits": split_df.to_dict("records")}
    )


@alphavantage_server.tool(
    name="get_financial_statement",
    description="""Get financial statement for a given ticker symbol using Alpha Vantage. Supported types: income_stmt_annual, income_stmt_quarterly, balance_sheet_annual, balance_sheet_quarterly, cashflow_annual, cashflow_quarterly.

Args:
    ticker: str
        The ticker symbol of the stock to get financial statement for, e.g. "AAPL"
    financial_type: str
        The type of financial statement to get. Use one of: income_stmt_annual, income_stmt_quarterly, balance_sheet_annual, balance_sheet_quarterly, cashflow_annual, cashflow_quarterly.
""",
)
async def get_financial_statement(ticker: str, financial_type: str) -> str:
    """Get financial statement for a given ticker symbol"""

    api_key = os.environ.get("ALPHAVANTAGE_API_KEY")
    if not api_key:
        return "Error: ALPHAVANTAGE_API_KEY environment variable not set."

    fd = FundamentalData(key=api_key)
    try:
        if financial_type == FinancialType.income_stmt_annual:
            data, _ = fd.get_income_statement_annual(symbol=ticker)
        elif financial_type == FinancialType.income_stmt_quarterly:
            data, _ = fd.get_income_statement_quarterly(symbol=ticker)
        elif financial_type == FinancialType.balance_sheet_annual:
            data, _ = fd.get_balance_sheet_annual(symbol=ticker)
        elif financial_type == FinancialType.balance_sheet_quarterly:
            data, _ = fd.get_balance_sheet_quarterly(symbol=ticker)
        elif financial_type == FinancialType.cashflow_annual:
            data, _ = fd.get_cash_flow_annual(symbol=ticker)
        elif financial_type == FinancialType.cashflow_quarterly:
            data, _ = fd.get_cash_flow_quarterly(symbol=ticker)
        else:
            return "Error: invalid financial type"
    except Exception as e:
        return f"Error: getting financial statement for {ticker}: {e}"

    return json.dumps(data)


@alphavantage_server.tool(
    name="get_option_expiration_dates",
    description="""Fetch the available options expiration dates for a given ticker symbol using Alpha Vantage.

Args:
    ticker: str
        The ticker symbol of the stock to get option expiration dates for, e.g. "AAPL"
""",
)
async def get_option_expiration_dates(ticker: str) -> str:
    """Fetch the available options expiration dates for a given ticker symbol."""

    api_key = os.environ.get("ALPHAVANTAGE_API_KEY")
    if not api_key:
        return "Error: ALPHAVANTAGE_API_KEY environment variable not set."

    opt = Options(key=api_key)
    try:
        data, _ = opt.get_realtime_options(symbol=ticker)
    except Exception as e:
        return f"Error: getting option expiration dates for {ticker}: {e}"

    if isinstance(data, pd.DataFrame):
        expirations = data["expiration"].dropna().astype(str).unique().tolist()
    else:
        expirations = {item.get("expiration") for item in data if item.get("expiration")}
    return json.dumps(sorted(expirations))


@alphavantage_server.tool(
    name="get_option_chain",
    description="""Fetch the option chain for a given ticker symbol, expiration date, and option type using Alpha Vantage.

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

    api_key = os.environ.get("ALPHAVANTAGE_API_KEY")
    if not api_key:
        return "Error: ALPHAVANTAGE_API_KEY environment variable not set."

    opt = Options(key=api_key)
    try:
        data, _ = opt.get_realtime_options(symbol=ticker)
    except Exception as e:
        return f"Error: getting option chain for {ticker}: {e}"

    if isinstance(data, pd.DataFrame):
        filtered = data[
            (data["expiration"] == expiration_date)
            & (data["type"].str.lower() == option_type.lower())
        ]
        return filtered.to_json(orient="records", date_format="iso")

    filtered = [
        item
        for item in data
        if item.get("expiration") == expiration_date
        and item.get("type", "").lower() == option_type.lower()
    ]
    return json.dumps(filtered)


if __name__ == "__main__":
    # Initialize and run the server
    print("Starting Alpha Vantage MCP server...")
    alphavantage_server.run(transport="stdio")
