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
""",
)


def _call_fmp_api(endpoint: str, params: dict) -> str:
    """Helper to call FMP API endpoints"""
    api_key = os.environ.get("FMP_API_KEY")
    if not api_key:
        return "Error: FMP_API_KEY environment variable not set."

    base = "https://financialmodelingprep.com/stable"
    try:
        resp = requests.get(
            f"{base}/{endpoint}",
            params={**params, "apikey": api_key},
            timeout=10,
        )
        resp.raise_for_status()
    except Exception as e:
        return f"Error: calling {endpoint}: {e}"

    try:
        return json.dumps(resp.json())
    except Exception:
        return resp.text


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
    name="search_financial_data",
    description="""根据不同类型的条件搜索金融数据，可选类型：symbol、name、cik、cusip、isin、exchange_variants。params 为额外查询参数的 JSON 字符串。""",
)
async def search_financial_data(search_type: str, params: str = "") -> str:
    mapping = {
        "symbol": "search-symbol",
        "name": "search-name",
        "cik": "search-cik",
        "cusip": "search-cusip",
        "isin": "search-isin",
        "exchange_variants": "search-exchange-variants",
    }
    endpoint = mapping.get(search_type)
    if not endpoint:
        return "Error: invalid search_type"
    extra = json.loads(params) if params else {}
    return _call_fmp_api(endpoint, extra)


@fmp_server.tool(
    name="list_directory_data",
    description="""获取目录类数据，类型包括：stock_list、financial_statement_symbol_list、cik_list、symbol_change、etf_list、actively_trading_list、earnings_transcript_list、available_exchanges、available_sectors、available_industries、available_countries。params 为额外查询参数的 JSON 字符串。""",
)
async def list_directory_data(list_type: str, params: str = "") -> str:
    mapping = {
        "stock_list": "stock-list",
        "financial_statement_symbol_list": "financial-statement-symbol-list",
        "cik_list": "cik-list",
        "symbol_change": "symbol-change",
        "etf_list": "etf-list",
        "actively_trading_list": "actively-trading-list",
        "earnings_transcript_list": "earnings-transcript-list",
        "available_exchanges": "available-exchanges",
        "available_sectors": "available-sectors",
        "available_industries": "available-industries",
        "available_countries": "available-countries",
    }
    endpoint = mapping.get(list_type)
    if not endpoint:
        return "Error: invalid list_type"
    extra = json.loads(params) if params else {}
    return _call_fmp_api(endpoint, extra)


@fmp_server.tool(
    name="analyst_data",
    description="""获取分析师相关数据，类型包括：financial_estimates、ratings_snapshot、ratings_historical、price_target_summary、price_target_consensus、price_target_news、price_target_latest_news、grades、grades_historical、grades_consensus、grades_news、grades_latest_news。params 为额外查询参数的 JSON 字符串。""",
)
async def analyst_data(data_type: str, params: str = "") -> str:
    mapping = {
        "financial_estimates": "analyst-estimates",
        "ratings_snapshot": "ratings-snapshot",
        "ratings_historical": "ratings-historical",
        "price_target_summary": "price-target-summary",
        "price_target_consensus": "price-target-consensus",
        "price_target_news": "price-target-news",
        "price_target_latest_news": "price-target-latest-news",
        "grades": "grades",
        "grades_historical": "grades-historical",
        "grades_consensus": "grades-consensus",
        "grades_news": "grades-news",
        "grades_latest_news": "grades-latest-news",
    }
    endpoint = mapping.get(data_type)
    if not endpoint:
        return "Error: invalid data_type"
    extra = json.loads(params) if params else {}
    return _call_fmp_api(endpoint, extra)


@fmp_server.tool(
    name="corporate_calendar",
    description="""获取企业日历数据，类型包括：dividends、dividends_calendar、earnings、earnings_calendar、ipos_calendar、ipos_disclosure、ipos_prospectus、splits、splits_calendar。params 为额外查询参数的 JSON 字符串。""",
)
async def corporate_calendar(calendar_type: str, params: str = "") -> str:
    mapping = {
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
    endpoint = mapping.get(calendar_type)
    if not endpoint:
        return "Error: invalid calendar_type"
    extra = json.loads(params) if params else {}
    return _call_fmp_api(endpoint, extra)


@fmp_server.tool(
    name="company_info_extended",
    description="""获取公司扩展信息，类型包括：profile_cik、company_notes、stock_peers、delisted_companies、employee_count、historical_employee_count、market_capitalization、market_capitalization_batch、historical_market_capitalization、shares_float、shares_float_all。params 为额外查询参数的 JSON 字符串。""",
)
async def company_info_extended(info_type: str, params: str = "") -> str:
    mapping = {
        "profile_cik": "profile-cik",
        "company_notes": "company-notes",
        "stock_peers": "stock-peers",
        "delisted_companies": "delisted-companies",
        "employee_count": "employee-count",
        "historical_employee_count": "historical-employee-count",
        "market_capitalization": "market-capitalization",
        "market_capitalization_batch": "market-capitalization-batch",
        "historical_market_capitalization": "historical-market-capitalization",
        "shares_float": "shares-float",
        "shares_float_all": "shares-float-all",
    }
    endpoint = mapping.get(info_type)
    if not endpoint:
        return "Error: invalid info_type"
    extra = json.loads(params) if params else {}
    return _call_fmp_api(endpoint, extra)


@fmp_server.tool(
    name="mergers_acquisitions",
    description="""获取并购相关信息，类型包括：latest、search。params 为额外查询参数的 JSON 字符串。""",
)
async def mergers_acquisitions(ma_type: str, params: str = "") -> str:
    mapping = {
        "latest": "mergers-acquisitions-latest",
        "search": "mergers-acquisitions-search",
    }
    endpoint = mapping.get(ma_type)
    if not endpoint:
        return "Error: invalid ma_type"
    extra = json.loads(params) if params else {}
    return _call_fmp_api(endpoint, extra)


@fmp_server.tool(
    name="cot_report",
    description="""获取COT报告相关数据，类型包括：report、analysis、list。params 为额外查询参数的 JSON 字符串。""",
)
async def cot_report(report_type: str, params: str = "") -> str:
    mapping = {
        "report": "commitment-of-traders-report",
        "analysis": "commitment-of-traders-analysis",
        "list": "commitment-of-traders-list",
    }
    endpoint = mapping.get(report_type)
    if not endpoint:
        return "Error: invalid report_type"
    extra = json.loads(params) if params else {}
    return _call_fmp_api(endpoint, extra)


@fmp_server.tool(
    name="dcf_valuation",
    description="""获取DCF估值数据，类型包括：discounted_cash_flow、levered_discounted_cash_flow、custom_discounted_cash_flow。params 为额外查询参数的 JSON 字符串。""",
)
async def dcf_valuation(dcf_type: str, params: str = "") -> str:
    mapping = {
        "discounted_cash_flow": "discounted-cash-flow",
        "levered_discounted_cash_flow": "levered-discounted-cash-flow",
        "custom_discounted_cash_flow": "custom-discounted-cash-flow",
    }
    endpoint = mapping.get(dcf_type)
    if not endpoint:
        return "Error: invalid dcf_type"
    extra = json.loads(params) if params else {}
    return _call_fmp_api(endpoint, extra)


@fmp_server.tool(
    name="crypto_market_data",
    description="""获取加密货币市场数据，类型包括：list、quote、quote_short、batch_quotes、historical_eod_light、historical_eod_full、intraday_1min、intraday_5min、intraday_1hour。params 为额外查询参数的 JSON 字符串。""",
)
async def crypto_market_data(data_type: str, params: str = "") -> str:
    mapping = {
        "list": "cryptocurrency-list",
        "quote": "quote",
        "quote_short": "quote-short",
        "batch_quotes": "batch-crypto-quotes",
        "historical_eod_light": "historical-price-eod/light",
        "historical_eod_full": "historical-price-eod/full",
        "intraday_1min": "historical-chart/1min",
        "intraday_5min": "historical-chart/5min",
        "intraday_1hour": "historical-chart/1hour",
    }
    endpoint = mapping.get(data_type)
    if not endpoint:
        return "Error: invalid data_type"
    extra = json.loads(params) if params else {}
    return _call_fmp_api(endpoint, extra)


@fmp_server.tool(
    name="crypto_news",
    description="""获取加密货币新闻，类型包括：latest、search。params 为额外查询参数的 JSON 字符串。""",
)
async def crypto_news(news_type: str, params: str = "") -> str:
    mapping = {
        "latest": "news/crypto-latest",
        "search": "news/crypto",
    }
    endpoint = mapping.get(news_type)
    if not endpoint:
        return "Error: invalid news_type"
    extra = json.loads(params) if params else {}
    return _call_fmp_api(endpoint, extra)


@fmp_server.tool(
    name="bulk_eod",
    description="""批量获取某天的收盘数据。date 为 YYYY-MM-DD 格式。params 为额外查询参数的 JSON 字符串。""",
)
async def bulk_eod(date: str, params: str = "") -> str:
    extra = json.loads(params) if params else {}
    extra["date"] = date
    return _call_fmp_api("eod-bulk", extra)


if __name__ == "__main__":
    # Initialize and run the server
    print("Starting Financial Modeling Prep MCP server...")
    fmp_server.run(transport="stdio")
