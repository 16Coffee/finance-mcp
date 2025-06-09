import json
import os

from dotenv import load_dotenv

load_dotenv()

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

本服务器通过 Financial Modeling Prep API 提供股票与财务数据。
使用这些工具前，请将环境变量 `FMP_API_KEY` 设置为你的 API 密钥。

可用工具：
- get_historical_stock_prices：获取指定股票的历史价格。
- get_stock_info：获取公司概况和关键指标。
- get_news_sentiment：获取股票相关新闻。
- get_stock_actions：获取股票分红与拆股记录。
- get_financial_statement：获取公司财报（收入表、资产负债表、现金流量表）。
- get_option_expiration_dates：获取股票可用的期权到期日。
- get_option_chain：获取期权链数据。
- search_companies：根据关键字搜索公司。
- get_top_gainers：获取今日涨幅榜。
- get_top_losers：获取今日跌幅榜。
- get_stock_grades：获取分析师最新评级。
- get_stock_grades_historical：获取分析师评级历史记录。
- get_stock_grades_summary：获取分析师评级汇总。
- get_stock_grade_news：获取指定股票的评级新闻。
- get_stock_grade_latest_news：获取最新评级新闻。
""",
)


@fmp_server.tool(
    name="get_historical_stock_prices",
    description="""获取指定股票的历史价格，返回日期、开盘价、最高价、最低价、收盘价和成交量。
参数说明：
    ticker: str
        股票代码，例如 "AAPL"
    period : str
        支持的周期：1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max；
        也可以使用开始和结束日期；默认 "1mo"
    interval : str
        支持的间隔：1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo；
        分钟级数据最多可追溯60天；默认 "1d"
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
        # Convert the Date column to datetime for proper comparison
        df["Date"] = pd.to_datetime(df["Date"])

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
    description="""获取公司概况及关键财务指标。

参数说明：
    ticker: str
        股票代码，例如 "AAPL"
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
    description="""获取指定股票的相关新闻列表。

参数说明：
    ticker: str
        股票代码，例如 "AAPL"
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
    description="""获取股票的分红与拆股历史。

参数说明：
    ticker: str
        股票代码，例如 "AAPL"
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
    description="""获取公司财报，类型包括年度/季度的收入表、资产负债表和现金流量表。

参数说明：
    ticker: str
        股票代码，例如 "AAPL"
    financial_type: str
        财报类型：income_stmt_annual、income_stmt_quarterly、balance_sheet_annual、balance_sheet_quarterly、cashflow_annual、cashflow_quarterly
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
    name="get_calendar_data",
    description="""获取分红、收益、IPO、拆股等日历信息。

参数说明：
    event_type: str
        可选值：dividends、dividends_calendar、earnings、earnings_calendar、
        ipos_calendar、ipos_disclosure、ipos_prospectus、splits、splits_calendar
    symbol: str
        部分类型需要股票代码
    page: int
        页码，默认 0
    limit: int
        返回数量，默认 100""",
)
async def get_calendar_data(
    event_type: str,
    symbol: str = "",
    page: int = 0,
    limit: int = 100,
) -> str:
    """根据事件类型获取相关日历数据"""

    api_key = os.environ.get("FMP_API_KEY")
    if not api_key:
        return "Error: FMP_API_KEY environment variable not set."

    base = "https://financialmodelingprep.com/stable"
    endpoint_map = {
        "dividends": "dividends",
        "dividends_calendar": "dividends-calendar",
        "earnings": "earnings",
        "earnings_calendar": "earnings-calendar",
        "ipos_calendar": "ipos-calendar",
        "ipos_disclosure": "ipos-disclosure",
        "ipos_prospectus": "ipos-prospectus",
        "splits": "splits",
        "splits_calendar": "splits-calendar",
    }
    endpoint = endpoint_map.get(event_type.lower())
    if not endpoint:
        return "Error: invalid event type"

    params = {"apikey": api_key}
    if event_type in ["dividends", "earnings", "splits"] and not symbol:
        return "Error: symbol is required for this event type"
    if symbol:
        params["symbol"] = symbol
    if event_type in ["ipos_calendar", "ipos_disclosure", "ipos_prospectus"]:
        params.update({"page": page, "limit": limit})

    url = f"{base}/{endpoint}"
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return f"Error: getting calendar data {event_type}: {e}"
    return json.dumps(data)


@fmp_server.tool(
    name="get_shares_float_info",
    description="""获取流通股数据或全部公司流通股列表。

参数说明：
    info_type: str
        single 或 all
    symbol: str
        查询单个公司时必填
    page: int
        列表分页，默认 0
    limit: int
        返回数量，默认 1000""",
)
async def get_shares_float_info(
    info_type: str,
    symbol: str = "",
    page: int = 0,
    limit: int = 1000,
) -> str:
    """获取流通股信息"""

    api_key = os.environ.get("FMP_API_KEY")
    if not api_key:
        return "Error: FMP_API_KEY environment variable not set."

    base = "https://financialmodelingprep.com/stable"
    endpoint_map = {
        "single": "shares-float",
        "all": "shares-float-all",
    }
    endpoint = endpoint_map.get(info_type.lower())
    if not endpoint:
        return "Error: invalid info type"

    params = {"apikey": api_key}
    if info_type == "single":
        if not symbol:
            return "Error: symbol is required for single type"
        params["symbol"] = symbol
    else:
        params.update({"page": page, "limit": limit})

    url = f"{base}/{endpoint}"
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return f"Error: getting shares float info {info_type}: {e}"
    return json.dumps(data)


@fmp_server.tool(
    name="get_ma_data",
    description="""获取并购相关数据。

参数说明：
    action_type: str
        latest 或 search
    name: str
        搜索模式下的公司名称
    page: int
        页码，默认 0
    limit: int
        返回数量，默认 100""",
)
async def get_ma_data(
    action_type: str,
    name: str = "",
    page: int = 0,
    limit: int = 100,
) -> str:
    """获取并购信息"""

    api_key = os.environ.get("FMP_API_KEY")
    if not api_key:
        return "Error: FMP_API_KEY environment variable not set."

    base = "https://financialmodelingprep.com/stable"
    endpoint_map = {
        "latest": "mergers-acquisitions-latest",
        "search": "mergers-acquisitions-search",
    }
    endpoint = endpoint_map.get(action_type.lower())
    if not endpoint:
        return "Error: invalid action type"

    params = {"apikey": api_key, "page": page, "limit": limit}
    if action_type == "search":
        if not name:
            return "Error: name is required for search"
        params["name"] = name

    url = f"{base}/{endpoint}"
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return f"Error: getting M&A data {action_type}: {e}"
    return json.dumps(data)


@fmp_server.tool(
    name="get_executive_info",
    description="""获取公司高管信息或薪酬数据。

参数说明：
    info_type: str
        executives、compensation 或 benchmark
    symbol: str
        当类型为 executives 或 compensation 时必填""",
)
async def get_executive_info(info_type: str, symbol: str = "") -> str:
    """获取公司高管或薪酬相关数据"""

    api_key = os.environ.get("FMP_API_KEY")
    if not api_key:
        return "Error: FMP_API_KEY environment variable not set."

    base = "https://financialmodelingprep.com/stable"
    endpoint_map = {
        "executives": "key-executives",
        "compensation": "governance-executive-compensation",
        "benchmark": "executive-compensation-benchmark",
    }
    endpoint = endpoint_map.get(info_type.lower())
    if not endpoint:
        return "Error: invalid info type"

    params = {"apikey": api_key}
    if info_type in ["executives", "compensation"]:
        if not symbol:
            return "Error: symbol is required for this info type"
        params["symbol"] = symbol

    url = f"{base}/{endpoint}"
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return f"Error: getting executive info {info_type} for {symbol}: {e}"
    return json.dumps(data)


@fmp_server.tool(
    name="get_dcf_valuation",
    description="""获取 DCF 或杠杆 DCF 估值数据。

参数说明：
    valuation_type: str
        dcf 或 levered
    symbol: str
        股票代码""",
)
async def get_dcf_valuation(valuation_type: str, symbol: str) -> str:
    """根据类型获取 DCF 估值"""

    api_key = os.environ.get("FMP_API_KEY")
    if not api_key:
        return "Error: FMP_API_KEY environment variable not set."

    base = "https://financialmodelingprep.com/stable"
    endpoint_map = {
        "dcf": "discounted-cash-flow",
        "levered": "levered-discounted-cash-flow",
    }
    endpoint = endpoint_map.get(valuation_type.lower())
    if not endpoint:
        return "Error: invalid valuation type"

    url = f"{base}/{endpoint}"
    try:
        resp = requests.get(url, params={"symbol": symbol, "apikey": api_key}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return f"Error: getting {valuation_type} DCF for {symbol}: {e}"
    return json.dumps(data)


@fmp_server.tool(
    name="get_economic_data",
    description="""获取宏观经济数据。

参数说明：
    data_type: str
        treasury_rates、economic_indicators、economic_calendar、market_risk_premium
    name: str
        经济指标名称，data_type 为 economic_indicators 时必填
    from_date: str
        起始日期，格式 YYYY-MM-DD
    to_date: str
        结束日期，格式 YYYY-MM-DD""",
)
async def get_economic_data(
    data_type: str,
    name: str = "",
    from_date: str = "",
    to_date: str = "",
) -> str:
    """根据类型获取经济数据"""

    api_key = os.environ.get("FMP_API_KEY")
    if not api_key:
        return "Error: FMP_API_KEY environment variable not set."

    base = "https://financialmodelingprep.com/stable"
    endpoint_map = {
        "treasury_rates": "treasury-rates",
        "economic_indicators": "economic-indicators",
        "economic_calendar": "economic-calendar",
        "market_risk_premium": "market-risk-premium",
    }
    endpoint = endpoint_map.get(data_type.lower())
    if not endpoint:
        return "Error: invalid data type"

    params = {"apikey": api_key}
    if data_type == "economic_indicators":
        if not name:
            return "Error: name is required for economic_indicators"
        params["name"] = name
    if from_date and to_date:
        params.update({"from": from_date, "to": to_date})

    url = f"{base}/{endpoint}"
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return f"Error: getting economic data {data_type}: {e}"
    return json.dumps(data)


@fmp_server.tool(
    name="get_option_expiration_dates",
    description="""获取指定股票可用的期权到期日。

参数说明：
    ticker: str
        股票代码，例如 "AAPL"
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
    description="""根据股票代码、到期日和期权类型获取期权链数据。

参数说明：
    ticker: str
        股票代码，例如 "AAPL"
    expiration_date: str
        期权到期日，格式为 'YYYY-MM-DD'
    option_type: str
        期权类型：'calls' 或 'puts'
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


@fmp_server.tool(
    name="search_companies",
    description="""根据关键字搜索公司信息。

参数说明：
    query: str
        搜索关键字
    limit: int
        返回结果数量，默认 10
    exchange: str
        交易所代码，可选
""",
)
async def search_companies(query: str, limit: int = 10, exchange: str = "") -> str:
    """根据关键字搜索公司"""

    api_key = os.environ.get("FMP_API_KEY")
    if not api_key:
        return "Error: FMP_API_KEY environment variable not set."

    params = {"query": query, "limit": limit, "apikey": api_key}
    if exchange:
        params["exchange"] = exchange

    url = "https://financialmodelingprep.com/api/v3/search"
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return f"Error: searching companies: {e}"
    return json.dumps(data)


@fmp_server.tool(
    name="get_top_gainers",
    description="""获取今日涨幅最大的股票列表。""",
)
async def get_top_gainers() -> str:
    """获取今日涨幅榜"""

    api_key = os.environ.get("FMP_API_KEY")
    if not api_key:
        return "Error: FMP_API_KEY environment variable not set."

    url = "https://financialmodelingprep.com/api/v3/stock_market/gainers"
    try:
        resp = requests.get(url, params={"apikey": api_key}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return f"Error: getting top gainers: {e}"
    return json.dumps(data)


@fmp_server.tool(
    name="get_top_losers",
    description="""获取今日跌幅最大的股票列表。""",
)
async def get_top_losers() -> str:
    """获取今日跌幅榜"""

    api_key = os.environ.get("FMP_API_KEY")
    if not api_key:
        return "Error: FMP_API_KEY environment variable not set."

    url = "https://financialmodelingprep.com/api/v3/stock_market/losers"
    try:
        resp = requests.get(url, params={"apikey": api_key}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return f"Error: getting top losers: {e}"
    return json.dumps(data)


@fmp_server.tool(
    name="get_stock_grades",
    description="""获取分析师最新评级。

参数说明：
    ticker: str
        股票代码，例如 "AAPL""",
)
async def get_stock_grades(ticker: str) -> str:
    """获取指定股票的分析师最新评级"""

    api_key = os.environ.get("FMP_API_KEY")
    if not api_key:
        return "Error: FMP_API_KEY environment variable not set."

    url = "https://financialmodelingprep.com/stable/grades"
    try:
        resp = requests.get(url, params={"symbol": ticker, "apikey": api_key}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return f"Error: getting stock grades for {ticker}: {e}"
    return json.dumps(data)


@fmp_server.tool(
    name="get_stock_grades_historical",
    description="""获取分析师评级历史记录。

参数说明：
    ticker: str
        股票代码，例如 "AAPL"
    limit: int
        返回记录数量，最大 1000，默认 100""",
)
async def get_stock_grades_historical(ticker: str, limit: int = 100) -> str:
    """获取分析师评级历史数据"""

    api_key = os.environ.get("FMP_API_KEY")
    if not api_key:
        return "Error: FMP_API_KEY environment variable not set."

    url = "https://financialmodelingprep.com/stable/grades-historical"
    try:
        resp = requests.get(
            url,
            params={"symbol": ticker, "limit": limit, "apikey": api_key},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return f"Error: getting historical grades for {ticker}: {e}"
    return json.dumps(data)


@fmp_server.tool(
    name="get_stock_grades_summary",
    description="""获取分析师评级汇总。

参数说明：
    ticker: str
        股票代码，例如 "AAPL""",
)
async def get_stock_grades_summary(ticker: str) -> str:
    """获取分析师评级汇总数据"""

    api_key = os.environ.get("FMP_API_KEY")
    if not api_key:
        return "Error: FMP_API_KEY environment variable not set."

    url = "https://financialmodelingprep.com/stable/grades-consensus"
    try:
        resp = requests.get(url, params={"symbol": ticker, "apikey": api_key}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return f"Error: getting grades summary for {ticker}: {e}"
    return json.dumps(data)


@fmp_server.tool(
    name="get_stock_grade_news",
    description="""获取指定股票的评级新闻。

参数说明：
    ticker: str
        股票代码，例如 "AAPL"
    page: int
        页码，默认 0
    limit: int
        每页数量，最大 100，默认 1""",
)
async def get_stock_grade_news(ticker: str, page: int = 0, limit: int = 1) -> str:
    """获取分析师评级相关新闻"""

    api_key = os.environ.get("FMP_API_KEY")
    if not api_key:
        return "Error: FMP_API_KEY environment variable not set."

    url = "https://financialmodelingprep.com/stable/grades-news"
    try:
        resp = requests.get(
            url,
            params={
                "symbol": ticker,
                "page": page,
                "limit": limit,
                "apikey": api_key,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return f"Error: getting grade news for {ticker}: {e}"
    return json.dumps(data)


@fmp_server.tool(
    name="get_stock_grade_latest_news",
    description="""获取最新评级新闻。

参数说明：
    page: int
        页码，默认 0
    limit: int
        每页数量，最大 1000，默认 10""",
)
async def get_stock_grade_latest_news(page: int = 0, limit: int = 10) -> str:
    """获取所有股票的最新评级新闻"""

    api_key = os.environ.get("FMP_API_KEY")
    if not api_key:
        return "Error: FMP_API_KEY environment variable not set."

    url = "https://financialmodelingprep.com/stable/grades-latest-news"
    try:
        resp = requests.get(
            url,
            params={"page": page, "limit": limit, "apikey": api_key},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return f"Error: getting latest grade news: {e}"
    return json.dumps(data)


@fmp_server.tool(
    name="lookup_identifier",
    description="""按标识类型查询股票代码、CIK、CUSIP 或 ISIN。

参数说明：
    identifier_type: str
        可选值：symbol、name、cik、cusip、isin、exchange_variant
    query: str
        对应的查询内容""",
)
async def lookup_identifier(identifier_type: str, query: str) -> str:
    """根据不同标识类型搜索证券信息"""

    api_key = os.environ.get("FMP_API_KEY")
    if not api_key:
        return "Error: FMP_API_KEY environment variable not set."

    base = "https://financialmodelingprep.com/stable"
    endpoint_map = {
        "symbol": ("search-symbol", "query"),
        "name": ("search-name", "query"),
        "cik": ("search-cik", "cik"),
        "cusip": ("search-cusip", "cusip"),
        "isin": ("search-isin", "isin"),
        "exchange_variant": ("search-exchange-variants", "symbol"),
    }
    ep = endpoint_map.get(identifier_type.lower())
    if not ep:
        return "Error: invalid identifier type"

    endpoint, param_name = ep
    url = f"{base}/{endpoint}"
    try:
        resp = requests.get(url, params={param_name: query, "apikey": api_key}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return f"Error: lookup failed for {query}: {e}"
    return json.dumps(data)


@fmp_server.tool(
    name="get_directory_list",
    description="""获取市场或公司目录列表。

参数说明：
    list_type: str
        可选值：stock、financial_statement_symbol、cik、symbol_change、etf、
        actively_trading、earnings_transcript、available_exchanges、
        available_sectors、available_industries、available_countries""",
)
async def get_directory_list(list_type: str) -> str:
    """根据目录类型获取对应列表数据"""

    api_key = os.environ.get("FMP_API_KEY")
    if not api_key:
        return "Error: FMP_API_KEY environment variable not set."

    base = "https://financialmodelingprep.com/stable"
    endpoint_map = {
        "stock": "stock-list",
        "financial_statement_symbol": "financial-statement-symbol-list",
        "cik": "cik-list",
        "symbol_change": "symbol-change",
        "etf": "etf-list",
        "actively_trading": "actively-trading-list",
        "earnings_transcript": "earnings-transcript-list",
        "available_exchanges": "available-exchanges",
        "available_sectors": "available-sectors",
        "available_industries": "available-industries",
        "available_countries": "available-countries",
    }
    endpoint = endpoint_map.get(list_type.lower())
    if not endpoint:
        return "Error: invalid list type"
    url = f"{base}/{endpoint}"
    try:
        resp = requests.get(url, params={"apikey": api_key}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return f"Error: getting directory list for {list_type}: {e}"
    return json.dumps(data)


@fmp_server.tool(
    name="get_analyst_estimates",
    description="""获取分析师的财务预估数据。

参数说明：
    symbol: str
        股票代码，例如 "AAPL"
    period: str
        annual 或 quarter，默认 annual
    page: int
        页码，默认 0
    limit: int
        返回数量，默认 10""",
)
async def get_analyst_estimates(
    symbol: str, period: str = "annual", page: int = 0, limit: int = 10
) -> str:
    """获取分析师预估指标"""

    api_key = os.environ.get("FMP_API_KEY")
    if not api_key:
        return "Error: FMP_API_KEY environment variable not set."

    url = "https://financialmodelingprep.com/stable/analyst-estimates"
    try:
        resp = requests.get(
            url,
            params={
                "symbol": symbol,
                "period": period,
                "page": page,
                "limit": limit,
                "apikey": api_key,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return f"Error: getting analyst estimates for {symbol}: {e}"
    return json.dumps(data)


@fmp_server.tool(
    name="get_ratings",
    description="""获取股票评级数据，可选择快照或历史记录。

参数说明：
    symbol: str
        股票代码，例如 "AAPL"
    rating_type: str
        snapshot 或 historical，默认 snapshot
    limit: int
        返回数量，默认 1""",
)
async def get_ratings(symbol: str, rating_type: str = "snapshot", limit: int = 1) -> str:
    """根据类型获取评级信息"""

    api_key = os.environ.get("FMP_API_KEY")
    if not api_key:
        return "Error: FMP_API_KEY environment variable not set."

    base = "https://financialmodelingprep.com/stable"
    endpoint_map = {
        "snapshot": "ratings-snapshot",
        "historical": "ratings-historical",
    }
    endpoint = endpoint_map.get(rating_type.lower())
    if not endpoint:
        return "Error: invalid rating type"
    url = f"{base}/{endpoint}"
    try:
        resp = requests.get(
            url,
            params={"symbol": symbol, "limit": limit, "apikey": api_key},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return f"Error: getting {rating_type} ratings for {symbol}: {e}"
    return json.dumps(data)


@fmp_server.tool(
    name="get_price_target_info",
    description="""获取分析师目标价相关信息，可选择汇总、共识或新闻。

参数说明：
    info_type: str
        summary、consensus、news、latest_news
    symbol: str
        股票代码，news/summary/consensus 必填
    page: int
        页码，默认 0
    limit: int
        返回数量，默认 10""",
)
async def get_price_target_info(
    info_type: str,
    symbol: str = "",
    page: int = 0,
    limit: int = 10,
) -> str:
    """获取价格目标汇总、共识或相关新闻"""

    api_key = os.environ.get("FMP_API_KEY")
    if not api_key:
        return "Error: FMP_API_KEY environment variable not set."

    base = "https://financialmodelingprep.com/stable"
    endpoint_map = {
        "summary": "price-target-summary",
        "consensus": "price-target-consensus",
        "news": "price-target-news",
        "latest_news": "price-target-latest-news",
    }
    endpoint = endpoint_map.get(info_type.lower())
    if not endpoint:
        return "Error: invalid info type"

    params = {"apikey": api_key}
    if info_type in ["summary", "consensus", "news"]:
        if not symbol:
            return "Error: symbol is required for this info type"
        params["symbol"] = symbol
    if info_type in ["news", "latest_news"]:
        params.update({"page": page, "limit": limit})

    url = f"{base}/{endpoint}"
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return f"Error: getting price target info {info_type} for {symbol}: {e}"
    return json.dumps(data)


if __name__ == "__main__":
    # Initialize and run the server
    print("Starting Financial Modeling Prep MCP server...")
    fmp_server.run(transport="stdio")
