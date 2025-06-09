[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/alex2yang97-financialmodelingprep-mcp-badge.png)](https://mseep.ai/app/alex2yang97-financialmodelingprep-mcp)

# Financial Modeling Prep MCP Server

<div align="right">
  <a href="README.md">English</a> | <a href="README.zh.md">中文</a>
</div>

This is a Model Context Protocol (MCP) server that provides comprehensive financial data from Financial Modeling Prep. It allows you to retrieve detailed information about stocks, including historical prices, company information, financial statements, options data, and market news.

[![smithery badge](https://smithery.ai/badge/@Alex2Yang97/financialmodelingprep-mcp)](https://smithery.ai/server/@Alex2Yang97/financialmodelingprep-mcp)

## Demo

![MCP Demo](assets/demo.gif)

## MCP Tools

The server exposes the following tools through the Model Context Protocol:

### Stock Information

| Tool | Description |
|------|-------------|
| `get_historical_stock_prices` | Get historical OHLCV data for a stock with customizable period and interval |
| `get_stock_info` | Get comprehensive stock data including price, metrics, and company details |
| `get_news_sentiment` | Get latest news articles for a stock |
| `get_stock_actions` | Get stock dividends and splits history |

### Financial Statements

| Tool | Description |
|------|-------------|
| `get_financial_statement` | Get income statement, balance sheet, or cash flow statement (annual/quarterly) using Financial Modeling Prep |

### Options Data

| Tool | Description |
|------|-------------|
| `get_option_expiration_dates` | Get available options expiration dates |
| `get_option_chain` | Get options chain for a specific expiration date and type (calls/puts) |

### Stock Grades

| Tool | Description |
|------|-------------|
| `get_stock_grades` | Get the latest analyst grades for a stock |
| `get_stock_grades_historical` | Get historical analyst grades |
| `get_stock_grades_summary` | Get a consensus summary of analyst grades |
| `get_stock_grade_news` | Get grade-related news for a stock |
| `get_stock_grade_latest_news` | Get the most recent analyst grade news |
| `get_analyst_estimates` | Retrieve analyst financial estimates |
| `get_ratings` | Get ratings snapshot or history |
| `get_price_target_info` | Get price target summary, consensus or news |

### Reference Data

| Tool | Description |
|------|-------------|
| `lookup_identifier` | Search by symbol, name, CIK, CUSIP or ISIN |
| `get_directory_list` | Retrieve exchange, sector and other lists |

### Corporate Events

| Tool | Description |
|------|-------------|
| `get_calendar_data` | Get dividends, earnings, IPO and split calendars |
| `get_shares_float_info` | Retrieve float data for one or all companies |
| `get_ma_data` | Get latest or search M&A transactions |
| `get_executive_info` | Fetch company executives or compensation info |
| `get_dcf_valuation` | Obtain DCF or levered DCF valuation |
| `get_economic_data` | Retrieve treasury rates and other macro data |

## Real-World Use Cases

With this MCP server, you can use Claude to:

### Stock Analysis

- **Price Analysis**: "Show me the historical stock prices for AAPL over the last 6 months with daily intervals."
- **Financial Health**: "Get the quarterly balance sheet for Microsoft."
- **Performance Metrics**: "What are the key financial metrics for Tesla from the stock info?"
- **Trend Analysis**: "Compare the quarterly income statements of Amazon and Google."
- **Cash Flow Analysis**: "Show me the annual cash flow statement for NVIDIA."

### Market Research

- **News Analysis**: "Get the latest news articles about Meta Platforms."
- **Market Movers**: "List today's top gainers and losers."
- **Options Analysis**: "Get the options chain for SPY with expiration date 2024-06-21 for calls."

### Investment Research

- "Create a comprehensive analysis of Microsoft's financial health using their latest quarterly financial statements."
- "Compare the dividend history and stock splits of Coca-Cola and PepsiCo."
- "Generate a report on the options market activity for Apple stock with expiration in 30 days."

## Requirements

- Python 3.11 or higher
- Dependencies as listed in `pyproject.toml`, including:
  - mcp
  - requests
  - pandas
  - pydantic
  - and other packages for data processing

## Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/Alex2Yang97/financialmodelingprep-mcp.git
   cd financialmodelingprep-mcp
   ```

2. Create and activate a virtual environment and install dependencies:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -e .
   ```

3. Set your Financial Modeling Prep API key:
   ```bash
   export FMP_API_KEY=YOUR_API_KEY
   ```

## Usage

### Development Mode

You can test the server with MCP Inspector by running:

```bash
uv run server.py
```

This will start the server and allow you to test the available tools.

### Integration with Claude for Desktop

To integrate this server with Claude for Desktop:

1. Install Claude for Desktop to your local machine.
2. Install VS Code to your local machine. Then run the following command to open the `claude_desktop_config.json` file:
   - MacOS: `code ~/Library/Application\ Support/Claude/claude_desktop_config.json`
   - Windows: `code $env:AppData\Claude\claude_desktop_config.json`

3. Edit the Claude for Desktop config file, located at:
   - macOS: 
     ```json
     {
       "mcpServers": {
         "financialmodelingprep": {
           "command": "uv",
           "args": [
             "--directory",
             "/ABSOLUTE/PATH/TO/PARENT/FOLDER/financialmodelingprep-mcp",
             "run",
             "server.py"
           ]
         }
       }
     }
     ```
   - Windows:
     ```json
     {
       "mcpServers": {
         "financialmodelingprep": {
           "command": "uv",
           "args": [
             "--directory",
             "C:\\ABSOLUTE\\PATH\\TO\\PARENT\\FOLDER\\financialmodelingprep-mcp",
             "run",
             "server.py"
           ]
         }
       }
     }
     ```

   - **Note**: You may need to put the full path to the uv executable in the command field. You can get this by running `which uv` on MacOS/Linux or `where uv` on Windows.

4. Restart Claude for Desktop

## License

MIT


