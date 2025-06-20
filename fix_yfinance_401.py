#!/usr/bin/env python3
"""
Fix YFinance 401 error by implementing proper headers and fallback mechanisms.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_yfinance_with_headers():
    """Test yfinance with proper headers to fix 401 error."""
    print("🔧 Testing YFinance with Headers Fix")
    print("=" * 50)
    
    try:
        import yfinance as yf
        import requests
        
        # Set up session with proper headers
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        print("🧪 Testing with custom headers...")
        ticker = yf.Ticker("NVDA", session=session)
        
        # Try different methods
        print("📊 Trying ticker.history()...")
        hist = ticker.history(period="1d")
        if not hist.empty:
            current_price = hist['Close'].iloc[-1]
            print(f"✅ Success! NVDA current price: ${current_price:.2f}")
            return True
        
        print("📊 Trying ticker.info...")
        info = ticker.info
        if info and 'currentPrice' in info:
            print(f"✅ Success! NVDA current price: ${info['currentPrice']}")
            return True
            
        print("⚠️  No price data available")
        return False
        
    except Exception as e:
        print(f"❌ Still getting error: {e}")
        return False


def test_alternative_apis():
    """Test alternative financial APIs."""
    print("\n🔄 Testing Alternative APIs")
    print("=" * 50)
    
    # Test Alpha Vantage (free tier)
    print("📈 Testing Alpha Vantage...")
    try:
        import requests
        
        # Free API key for testing (limited requests)
        api_key = "demo"  # Replace with real key for production
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=NVDA&apikey={api_key}"
        
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "Global Quote" in data:
                price = data["Global Quote"]["05. price"]
                print(f"✅ Alpha Vantage success! NVDA: ${price}")
                return True
        
        print("⚠️  Alpha Vantage demo key limited")
        
    except Exception as e:
        print(f"❌ Alpha Vantage error: {e}")
    
    # Test Yahoo Finance alternative endpoint
    print("\n📊 Testing Yahoo Finance alternative endpoint...")
    try:
        import requests
        
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/NVDA"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "chart" in data and data["chart"]["result"]:
                price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
                print(f"✅ Yahoo alternative endpoint success! NVDA: ${price}")
                return True
        
        print(f"⚠️  Yahoo alternative returned {response.status_code}")
        
    except Exception as e:
        print(f"❌ Yahoo alternative error: {e}")
    
    return False


def create_mock_yfinance_tool():
    """Create a mock YFinance tool for testing."""
    print("\n🎭 Creating Mock YFinance Tool")
    print("=" * 50)
    
    mock_data = {
        "NVDA": {"price": 875.50, "name": "NVIDIA Corporation"},
        "AAPL": {"price": 225.75, "name": "Apple Inc."},
        "MSFT": {"price": 415.25, "name": "Microsoft Corporation"},
        "GOOGL": {"price": 175.80, "name": "Alphabet Inc."},
        "TSLA": {"price": 248.90, "name": "Tesla, Inc."},
    }
    
    def mock_get_current_stock_price(symbol: str) -> str:
        """Mock function that returns fake stock data."""
        symbol = symbol.upper()
        if symbol in mock_data:
            data = mock_data[symbol]
            return f"${data['price']} - {data['name']} (Mock Data)"
        else:
            return f"Mock data not available for {symbol}"
    
    # Test the mock function
    print("🧪 Testing mock function...")
    result = mock_get_current_stock_price("NVDA")
    print(f"✅ Mock result: {result}")
    
    return mock_get_current_stock_price


async def main():
    """Main function to test all solutions."""
    print("🚀 YFinance 401 Error Fix Script")
    print("=" * 50)
    
    # Try headers fix first
    if test_yfinance_with_headers():
        print("\n🎉 Headers fix worked! YFinance is functional.")
        return
    
    # Try alternative APIs
    if test_alternative_apis():
        print("\n🎉 Alternative API worked!")
        return
    
    # Create mock tool as fallback
    print("\n📝 All external APIs failed, creating mock tool...")
    mock_func = create_mock_yfinance_tool()
    
    print("\n💡 Solutions Summary:")
    print("1. ✅ Mock data tool created for testing")
    print("2. 🔧 Headers fix attempted (may need API key)")
    print("3. 🔄 Alternative APIs tested")
    print("\n📋 Next Steps:")
    print("- Get Alpha Vantage API key for production")
    print("- Implement retry logic with delays")
    print("- Use mock data for development/testing")


if __name__ == "__main__":
    asyncio.run(main())
