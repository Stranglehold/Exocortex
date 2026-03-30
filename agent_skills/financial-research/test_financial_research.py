"""
Tests for Financial Research Skill
"""

import sys
sys.path.insert(0, '/a0/skills/financial-research')

from financial_research import (
    get_income_statements,
    get_balance_sheets,
    get_cash_flow_statements,
    get_company_profile
)

def test_get_income_statements():
    """Test income statement retrieval."""
    data = get_income_statements("AAPL", period="annual", limit=3)
    assert isinstance(data, list), "Should return a list"
    if len(data) > 0:
        assert "date" in data[0] or "periodEnding" in data[0], "Should have date field"
        print(f"✓ Retrieved {len(data)} income statement periods")

def test_get_balance_sheets():
    """Test balance sheet retrieval."""
    data = get_balance_sheets("AAPL", period="annual", limit=3)
    assert isinstance(data, list), "Should return a list"
    if len(data) > 0:
        print(f"✓ Retrieved {len(data)} balance sheet periods")

def test_get_cash_flow_statements():
    """Test cash flow statement retrieval."""
    data = get_cash_flow_statements("AAPL", period="annual", limit=3)
    assert isinstance(data, list), "Should return a list"
    if len(data) > 0:
        print(f"✓ Retrieved {len(data)} cash flow periods")

def test_get_company_profile():
    """Test company profile retrieval."""
    data = get_company_profile("AAPL")
    assert isinstance(data, dict), "Should return a dict"
    print(f"✓ Retrieved company profile with {len(data)} fields")

if __name__ == "__main__":
    print("Running Financial Research Skill Tests...
")

    try:
        test_get_income_statements()
    except Exception as e:
        print(f"✗ Income statements test failed: {e}")

    try:
        test_get_balance_sheets()
    except Exception as e:
        print(f"✗ Balance sheets test failed: {e}")

    try:
        test_get_cash_flow_statements()
    except Exception as e:
        print(f"✗ Cash flow statements test failed: {e}")

    try:
        test_get_company_profile()
    except Exception as e:
        print(f"✗ Company profile test failed: {e}")

    print("
Tests complete.")
