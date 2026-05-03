"""Utility functions for parsing MCP responses."""

import re
from typing import Any, Optional, Dict, List


def parse_ticker_info(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse ticker info response from MCP.
    
    Args:
        response: Raw MCP response
        
    Returns:
        Dictionary with parsed ticker data including current_price
    """
    if "error" in response:
        return {"error": response["error"]}
    
    # Extract content from MCP response
    content = response.get("content", [])
    if not content:
        return {"error": "No content in response"}
    
    # Get text content
    text_content = ""
    for item in content:
        if isinstance(item, dict) and item.get("type") == "text":
            text_content = item.get("text", "")
            break
    
    if not text_content:
        return {"error": "No text content found"}
    
    # Parse markdown table or text for price
    parsed = {}
    
    # Try to extract current price from various formats
    # Format 1: "currentPrice": 280.14
    price_match = re.search(r'"currentPrice":\s*([\d,]+\.?\d*)', text_content)
    if price_match:
        price_str = price_match.group(1).replace(",", "")
        try:
            parsed["current_price"] = float(price_str)
        except ValueError:
            pass
    
    # Format 2: "regularMarketPrice": 280.14
    if "current_price" not in parsed:
        price_match = re.search(r'"regularMarketPrice":\s*([\d,]+\.?\d*)', text_content)
        if price_match:
            price_str = price_match.group(1).replace(",", "")
            try:
                parsed["current_price"] = float(price_str)
            except ValueError:
                pass
    
    # Format 3: Current Price: $280.14
    if "current_price" not in parsed:
        price_match = re.search(r"Current Price[:\s]+\$?([\d,]+\.?\d*)", text_content, re.IGNORECASE)
        if price_match:
            price_str = price_match.group(1).replace(",", "")
            try:
                parsed["current_price"] = float(price_str)
            except ValueError:
                pass
    
    # Try to extract company name
    # Format 1: "shortName": "Apple Inc."
    name_match = re.search(r'"shortName":\s*"([^"]+)"', text_content)
    if name_match:
        parsed["company_name"] = name_match.group(1).strip()
    
    # Format 2: Company: Apple Inc.
    if "company_name" not in parsed:
        name_match = re.search(r"Company[:\s]+(.+?)(?:\n|$)", text_content, re.IGNORECASE)
        if name_match:
            parsed["company_name"] = name_match.group(1).strip()
    
    # Store raw text for fallback
    parsed["raw_text"] = text_content
    
    return parsed


def parse_price_history(response: Dict[str, Any]) -> List[float]:
    """
    Parse price history response from MCP.
    
    Args:
        response: Raw MCP response with historical data
        
    Returns:
        List of closing prices
    """
    if "error" in response:
        return []
    
    # Extract content from MCP response
    content = response.get("content", [])
    if not content:
        return []
    
    # Get text content
    text_content = ""
    for item in content:
        if isinstance(item, dict) and item.get("type") == "text":
            text_content = item.get("text", "")
            break
    
    if not text_content:
        return []
    
    # Parse markdown table for closing prices
    prices = []
    
    # Look for Close column in markdown table
    lines = text_content.split("\n")
    close_col_idx = None
    
    for line in lines:
        # Find header row
        if "Close" in line and "|" in line:
            headers = [h.strip() for h in line.split("|")]
            try:
                close_col_idx = headers.index("Close")
            except ValueError:
                continue
        
        # Parse data rows
        elif close_col_idx is not None and "|" in line and not line.startswith("|---"):
            cols = [c.strip() for c in line.split("|")]
            if len(cols) > close_col_idx:
                price_str = cols[close_col_idx].replace("$", "").replace(",", "").strip()
                try:
                    price = float(price_str)
                    prices.append(price)
                except ValueError:
                    continue
    
    return prices


def calculate_return(prices: List[float]) -> Optional[float]:
    """
    Calculate return from price history.
    
    Args:
        prices: List of prices (oldest to newest)
        
    Returns:
        Return as decimal (e.g., 0.15 for 15% return), or None if insufficient data
    """
    if len(prices) < 2:
        return None
    
    start_price = prices[0]
    end_price = prices[-1]
    
    if start_price <= 0:
        return None
    
    return (end_price - start_price) / start_price


def extract_fx_rate(response: Dict[str, Any], from_currency: str, to_currency: str) -> Optional[float]:
    """
    Extract FX rate from ticker info response.
    
    Args:
        response: MCP response for FX pair (e.g., EURUSD=X)
        from_currency: Source currency
        to_currency: Target currency
        
    Returns:
        Exchange rate, or None if not found
    """
    parsed = parse_ticker_info(response)
    
    if "current_price" in parsed:
        return parsed["current_price"]
    
    # Try to parse from raw text
    if "raw_text" in parsed:
        text = parsed["raw_text"]
        # Look for rate in text
        rate_match = re.search(r"([\d,]+\.?\d+)", text)
        if rate_match:
            rate_str = rate_match.group(1).replace(",", "")
            try:
                return float(rate_str)
            except ValueError:
                pass
    
    return None
