# Financial Research Skill

## Overview
Domain-specialized skill for financial data research and analysis. Provides access to income statements, balance sheets, cash flow statements, and market data.

Inspired by Dexter's domain-specific tool design pattern.

## Capabilities
- Retrieve income statements (annual/quarterly)
- Access balance sheet data
- Fetch cash flow statements
- Get company fundamentals
- Market data queries

## Dependencies
```bash
pip install requests python-dotenv
```

## Configuration
Set environment variable:
```bash
export FINANCIAL_DATASETS_API_KEY="your-api-key-here"
```

Get API key from: https://financialdatasets.ai

Note: AAPL, NVDA, MSFT data is free. Other tickers require paid tier.

## Usage Examples

### Python Import
```python
from financial_research import get_income_statements, get_balance_sheets, get_cash_flow

# Get Apple's last 5 annual income statements
data = get_income_statements("AAPL", period="annual", limit=5)
print(data[0])  # Most recent year
```

### Command Line
```bash
python -c "from skills.financial_research import get_income_statements; print(get_income_statements('AAPL', 'annual', 3))"
```

## API Reference

### get_income_statements(ticker, period="annual", limit=5)
Retrieve income statement data.
- `ticker`: Stock symbol (e.g., "AAPL", "TSLA")
- `period`: "annual" or "quarterly"
- `limit`: Number of periods to retrieve (default: 5)

Returns list of dicts with keys: date, revenue, netIncome, operatingIncome, etc.

### get_balance_sheets(ticker, period="annual", limit=5)
Retrieve balance sheet data.
- Same parameters as get_income_statements

Returns list of dicts with keys: date, totalAssets, totalLiabilities, shareholdersEquity, etc.

### get_cash_flow_statements(ticker, period="annual", limit=5)
Retrieve cash flow statement data.
- Same parameters as get_income_statements

Returns list of dicts with keys: date, operatingCashFlow, investingCashFlow, financingCashFlow, etc.

## Data Sources
- **Primary**: Financial Datasets API (https://financialdatasets.ai)
- **Fallback**: Yahoo Finance via yfinance library (limited data)

## Limitations
- Free tier limited to AAPL, NVDA, MSFT
- Rate limits apply based on subscription tier
- Historical data depth varies by ticker and subscription

## Testing
```bash
cd /a0/skills/financial-research
python test_financial_research.py
```
