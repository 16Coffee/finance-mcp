# Financial Modeling Prep MCP 服务器

<div align="right">
  <a href="README.md">English</a> | <a href="README.zh.md">中文</a>
</div>

这是一个基于模型上下文协议（MCP）的服务器，提供来自 Financial Modeling Prep 的全面金融数据。它允许您获取股票的详细信息，包括历史价格、公司信息、财务报表、期权数据和市场新闻。

[![smithery badge](https://smithery.ai/badge/@Alex2Yang97/financialmodelingprep-mcp)](https://smithery.ai/server/@Alex2Yang97/financialmodelingprep-mcp)

## 演示

![MCP 演示](assets/demo.gif)

## MCP 工具

服务器通过模型上下文协议提供以下工具：

### 股票信息

| 工具 | 描述 |
|------|-------------|
| `get_historical_stock_prices` | 获取股票的历史 OHLCV 数据，可自定义时间段和间隔 |
| `get_stock_info` | 获取全面的股票数据，包括价格、指标和公司详情 |
| `get_news_sentiment` | 获取股票的最新新闻文章 |
| `get_stock_actions` | 获取股票分红和拆股历史 |

### 财务报表

| 工具 | 描述 |
|------|-------------|
| `get_financial_statement` | 使用 Financial Modeling Prep 获取利润表、资产负债表或现金流量表（年度/季度） |

### 期权数据

| 工具 | 描述 |
|------|-------------|
| `get_option_expiration_dates` | 获取可用的期权到期日期 |
| `get_option_chain` | 获取特定到期日期和类型（看涨/看跌）的期权链 |

### 分析师评级

| 工具 | 描述 |
|------|-------------|
| `get_stock_grades` | 获取股票的最新分析师评级 |
| `get_stock_grades_historical` | 获取分析师评级历史记录 |
| `get_stock_grades_summary` | 获取分析师评级汇总信息 |
| `get_stock_grade_news` | 获取该股票相关的评级新闻 |
| `get_stock_grade_latest_news` | 获取最新的分析师评级新闻 |
| `get_analyst_estimates` | 获取分析师财务预估 |
| `get_ratings` | 获取评级快照或历史数据 |
| `get_price_target_info` | 获取目标价汇总、共识或相关新闻 |

### 参考数据

| 工具 | 描述 |
|------|-------------|
| `lookup_identifier` | 按股票代码、名称、CIK、CUSIP 或 ISIN 查询 |
| `get_directory_list` | 获取交易所、行业等目录列表 |

### 公司事件

| 工具 | 描述 |
|------|-------------|
| `get_calendar_data` | 获取分红、收益、IPO、拆股等日历信息 |
| `get_shares_float_info` | 获取单家公司或全部公司的流通股数据 |
| `get_ma_data` | 获取最新并购交易或按名称搜索 |
| `get_executive_info` | 获取公司高管或薪酬信息 |
| `get_dcf_valuation` | 获取 DCF 或杠杆 DCF 估值 |
| `get_economic_data` | 获取国债利率等宏观经济数据 |

### 加密货币数据

| 工具 | 描述 |
|------|------|
| `get_crypto_list` | 获取可交易的加密货币列表 |
| `get_crypto_quote` | 获取加密货币完整行情 |
| `get_crypto_quote_short` | 获取加密货币简要行情 |
| `get_all_crypto_quotes` | 获取所有加密货币的实时行情 |
| `get_crypto_price_eod` | 获取加密货币历史收盘价，可选简略或完整模式 |
| `get_crypto_intraday` | 以 1min、5min 或 1hour 间隔获取加密货币分时数据 |
| `get_crypto_news` | 搜索加密货币相关新闻 |
| `get_crypto_latest_news` | 获取最新的加密货币新闻 |

## 实际应用场景

使用此 MCP 服务器，您可以利用 Claude 进行：

### 股票分析

- **价格分析**："显示苹果公司过去 6 个月的每日历史股价。"
- **财务健康**："获取微软的季度资产负债表。"
- **业绩指标**："从股票信息中获取特斯拉的关键财务指标。"
- **趋势分析**："比较亚马逊和谷歌的季度利润表。"
- **现金流分析**："显示英伟达的年度现金流量表。"

### 市场研究

- **新闻分析**："获取关于 Meta Platforms 的最新新闻文章。"
- **市场动态**："列出今日涨幅和跌幅最大的股票。"
- **期权分析**："获取 SPY 在 2024-06-21 到期的看涨期权链。"

### 投资研究

- "使用微软最新的季度财务报表创建其财务健康状况的全面分析。"
- "比较可口可乐和百事可乐的分红历史和股票拆分。"
 - "生成一份关于苹果股票 30 天到期的期权市场活动报告。"

## 系统要求

- Python 3.11 或更高版本
- `pyproject.toml` 中列出的依赖项，包括：
  - mcp
  - requests
  - pandas
  - pydantic
  - 以及其他数据处理包

## 安装

1. 克隆此仓库：
   ```bash
   git clone https://github.com/Alex2Yang97/financialmodelingprep-mcp.git
   cd financialmodelingprep-mcp
   ```

2. 创建并激活虚拟环境，安装依赖：
   ```bash
   uv venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
 uv pip install -e .
  ```

3. 设置 Financial Modeling Prep API 密钥：
   ```bash
   export FMP_API_KEY=你的 API 密钥
   ```

## 使用方法

### 开发模式

您可以通过运行以下命令使用 MCP Inspector 测试服务器：

```bash
uv run server.py
```

这将启动服务器并允许您测试可用工具。

### 与 Claude Desktop 集成

要将此服务器与 Claude Desktop 集成：

1. 在本地机器上安装 Claude Desktop。
2. 在本地机器上安装 VS Code。然后运行以下命令打开 `claude_desktop_config.json` 文件：
   - MacOS：`code ~/Library/Application\ Support/Claude/claude_desktop_config.json`
   - Windows：`code $env:AppData\Claude\claude_desktop_config.json`

3. 编辑 Claude Desktop 配置文件，位于：
   - macOS：
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
   - Windows：
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

   - **注意**：您可能需要在命令字段中填入 uv 可执行文件的完整路径。您可以通过在 MacOS/Linux 上运行 `which uv` 或在 Windows 上运行 `where uv` 来获取此路径。

4. 重启 Claude Desktop

## 许可证

MIT 