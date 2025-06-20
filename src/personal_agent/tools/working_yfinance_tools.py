"""
Working YFinance tools that bypass the 401 error using alternative endpoints.
"""

import requests
from typing import Optional
from agno.tools import Toolkit


class WorkingYFinanceTools(Toolkit):
    """Working YFinance tools using alternative Yahoo Finance endpoints."""

    def __init__(self, **kwargs):
        """Initialize the working YFinance tools."""
        super().__init__(
            name="working_yfinance",
            tools=[self.get_current_stock_price, self.get_stock_info],
            **kwargs
        )

    def get_current_stock_price(self, symbol: str) -> str:
        """Get the current stock price for a given symbol using working Yahoo Finance endpoint.

        Args:
            symbol (str): The stock symbol (e.g., 'NVDA', 'AAPL')

        Returns:
            str: The current stock price and basic info
        """
        try:
            symbol = symbol.upper().strip()
            
            # Use the working Yahoo Finance chart endpoint
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return f"Error: Unable to fetch data for {symbol} (HTTP {response.status_code})"
            
            data = response.json()
            
            if "chart" not in data or not data["chart"]["result"]:
                return f"Error: No data available for symbol {symbol}"
            
            result = data["chart"]["result"][0]
            meta = result["meta"]
            
            # Extract key information
            current_price = meta.get("regularMarketPrice", "N/A")
            currency = meta.get("currency", "USD")
            exchange = meta.get("exchangeName", "Unknown")
            company_name = meta.get("longName", symbol)
            
            # Calculate change if previous close is available
            prev_close = meta.get("previousClose")
            change_info = ""
            if prev_close and current_price != "N/A":
                change = current_price - prev_close
                change_percent = (change / prev_close) * 100
                change_symbol = "+" if change >= 0 else ""
                change_info = f" ({change_symbol}{change:.2f}, {change_symbol}{change_percent:.2f}%)"
            
            return f"💰 {symbol}: ${current_price:.2f} {currency}{change_info}\n📊 {company_name} on {exchange}"
            
        except requests.exceptions.RequestException as e:
            return f"Network error fetching {symbol}: {str(e)}"
        except Exception as e:
            return f"Error fetching {symbol}: {str(e)}"

    def get_stock_info(self, symbol: str) -> str:
        """Get detailed stock information for a given symbol.

        Args:
            symbol (str): The stock symbol (e.g., 'NVDA', 'AAPL')

        Returns:
            str: Detailed stock information
        """
        try:
            symbol = symbol.upper().strip()
            
            # Use the working Yahoo Finance chart endpoint
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return f"Error: Unable to fetch data for {symbol} (HTTP {response.status_code})"
            
            data = response.json()
            
            if "chart" not in data or not data["chart"]["result"]:
                return f"Error: No data available for symbol {symbol}"
            
            result = data["chart"]["result"][0]
            meta = result["meta"]
            
            # Extract comprehensive information
            info_parts = []
            info_parts.append(f"📈 **{symbol} - {meta.get('longName', 'Unknown Company')}**")
            info_parts.append(f"💰 Current Price: ${meta.get('regularMarketPrice', 'N/A'):.2f} {meta.get('currency', 'USD')}")
            
            if meta.get('previousClose'):
                prev_close = meta['previousClose']
                current = meta.get('regularMarketPrice', prev_close)
                change = current - prev_close
                change_percent = (change / prev_close) * 100
                change_symbol = "+" if change >= 0 else ""
                info_parts.append(f"📊 Change: {change_symbol}{change:.2f} ({change_symbol}{change_percent:.2f}%)")
            
            if meta.get('regularMarketDayHigh'):
                info_parts.append(f"📈 Day High: ${meta['regularMarketDayHigh']:.2f}")
            
            if meta.get('regularMarketDayLow'):
                info_parts.append(f"📉 Day Low: ${meta['regularMarketDayLow']:.2f}")
            
            if meta.get('regularMarketVolume'):
                volume = meta['regularMarketVolume']
                if volume > 1000000:
                    volume_str = f"{volume/1000000:.1f}M"
                elif volume > 1000:
                    volume_str = f"{volume/1000:.1f}K"
                else:
                    volume_str = str(volume)
                info_parts.append(f"📊 Volume: {volume_str}")
            
            info_parts.append(f"🏢 Exchange: {meta.get('exchangeName', 'Unknown')}")
            info_parts.append(f"🕐 Market Status: {meta.get('marketState', 'Unknown')}")
            
            return "\n".join(info_parts)
            
        except requests.exceptions.RequestException as e:
            return f"Network error fetching {symbol}: {str(e)}"
        except Exception as e:
            return f"Error fetching {symbol}: {str(e)}"


# Test function
def test_working_tools():
    """Test the working YFinance tools."""
    print("🧪 Testing Working YFinance Tools")
    print("=" * 50)
    
    tools = WorkingYFinanceTools()
    
    # Test current price
    print("📊 Testing get_current_stock_price('NVDA')...")
    result = tools.get_current_stock_price("NVDA")
    print(f"Result: {result}")
    
    print("\n📋 Testing get_stock_info('NVDA')...")
    result = tools.get_stock_info("NVDA")
    print(f"Result: {result}")


if __name__ == "__main__":
    test_working_tools()
