"""
Financial Research Module - Domain-specialized financial data access

Provides clean interfaces for income statements, balance sheets, and cash flow data.
"""

import os
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime

class FinancialResearchError(Exception):
    """Custom exception for financial research errors."""
    pass

def _get_api_key():
    """Get API key from environment."""
    api_key = os.environ.get("FINANCIAL_DATASETS_API_KEY")
    if not api_key:
        return None  # Will use free tier or fallback
    return api_key

def _make_request(endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Make API request to Financial Datasets API."""
    api_key = _get_api_key()

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    base_url = "https://api.financialdatasets.ai"
    url = f"{base_url}/{endpoint}"

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        # Fallback to yfinance if API fails
        return _fallback_yfinance(endpoint, params)

def _fallback_yfinance(endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback to yfinance when Financial Datasets API is unavailable."""
    try:
        import yfinance as yf
        ticker = params.get("ticker", "AAPL")

        if "income" in endpoint:
           yf_data = yf.Ticker(ticker).income_stmt
            return {"data": yf_data.to_dict() if hasattr(yf_data, 'to_dict') else []}
        elif "balance" in endpoint:
            bs_data = yf.Ticker(ticker).balance_sheet
            return {"data": bs_data.to_dict() if hasattr(bs_data, 'to_dict') else []}
        elif "cash-flow" in endpoint:
            cf_data = yf.Ticker(ticker).cashflow
            return {"data": cf_data.to_dict() if hasattr(cf_data, 'to_dict') else []}
    except Exception as e:
        pass  # Return empty on complete failure

    return {"data": [], "error": "Fallback also failed", "source": "none"}

def get_income_statements(
    ticker: str,
    period: str = "annual",
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Retrieve income statement data for a ticker.

    Args:
        ticker: Stock symbol (e.g., "AAPL", "TSLA")
        period: "annual" or "quarterly"
        limit: Number of periods to retrieve

    Returns:
        List of income statement dicts, most recent first
    """
    endpoint = f"stocks/{ticker}/income-statements"
    params = {"period": period, "limit": limit}

    response = _make_request(endpoint, params)
    return response.get("data", [])

def get_balance_sheets(
    ticker: str,
    period: str = "annual",
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Retrieve balance sheet data for a ticker.

    Args:
        ticker: Stock symbol
        period: "annual" or "quarterly"
        limit: Number of periods to retrieve

    Returns:
        List of balance sheet dicts, most recent first
    """
    endpoint = f"stocks/{ticker}/balance-sheets"
    params = {"period": period, "limit": limit}

    response = _make_request(endpoint, params)
    return response.get("data", [])

def get_cash_flow_statements(
    ticker: str,
    period: str = "annual",
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Retrieve cash flow statement data for a ticker.

    Args:
        ticker: Stock symbol
        period: "annual" or "quarterly"
        limit: Number of periods to retrieve

    Returns:
        List of cash flow dicts, most recent first
    """
    endpoint = f"stocks/{ticker}/cash-flow-statements"
    params = {"period": period, "limit": limit}

    response = _make_request(endpoint, params)
    return response.get("data", [])

def get_company_profile(ticker: str) -> Dict[str, Any]:
    """
    Retrieve company profile/fundamentals.

    Args:
        ticker: Stock symbol

    Returns:
        Company profile dict
    """
    endpoint = f"stocks/{ticker}/profile"
    response = _make_request(endpoint, {})
    return response.get("data", {})

def get_price_history(
    ticker: str,
    period: str = "1y",
    interval: str = "1d"
) -> List[Dict[str, Any]]:
    """
    Retrieve historical price data.

    Args:
        ticker: Stock symbol
        period: Time period ("1mo", "3mo", "6mo", "1y", "2y", "5y", "max")
        interval: Data interval ("1m", "5m", "15m", "30m", "1h", "1d", "1wk", "1mo")

    Returns:
        List of price data dicts
    """
    endpoint = f"stocks/{ticker}/price-history"
    params = {"period": period, "interval": interval}

    response = _make_request(endpoint, params)
    return response.get("data", [])
