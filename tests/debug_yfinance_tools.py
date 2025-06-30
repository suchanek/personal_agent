#!/usr/bin/env python3
"""
Debug script to test YFinance tools directly and diagnose errors.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agno.tools.yfinance import YFinanceTools


async def test_yfinance_tools():
    """Test YFinance tools directly to see what errors occur."""
    print("🧪 Testing YFinance Tools Directly")
    print("=" * 50)
    
    # Initialize YFinance tools
    print("📊 Initializing YFinanceTools...")
    try:
        yf_tools = YFinanceTools()
        print("✅ YFinanceTools initialized successfully")
        
        # Check what tools are available
        print(f"📋 Available tools: {len(yf_tools.tools)}")
        for tool in yf_tools.tools:
            print(f"   - {tool.__name__}")
        
    except Exception as e:
        print(f"❌ Failed to initialize YFinanceTools: {e}")
        return
    
    print("\n" + "=" * 50)
    print("🔍 Testing get_current_stock_price with NVDA")
    print("=" * 50)
    
    # Test get_current_stock_price directly
    try:
        # Find the get_current_stock_price function
        get_price_func = None
        for tool in yf_tools.tools:
            if hasattr(tool, '__name__') and tool.__name__ == 'get_current_stock_price':
                get_price_func = tool
                break
        
        if get_price_func is None:
            print("❌ get_current_stock_price function not found")
            print("Available functions:")
            for tool in yf_tools.tools:
                print(f"   - {getattr(tool, '__name__', str(tool))}")
            return
        
        print(f"✅ Found function: {get_price_func.__name__}")
        print(f"📝 Function signature: {get_price_func.__doc__}")
        
        # Test the function call
        print("\n🚀 Calling get_current_stock_price('NVDA')...")
        
        # Check if it's async or sync
        import inspect
        if inspect.iscoroutinefunction(get_price_func):
            print("   (Function is async)")
            result = await get_price_func("NVDA")
        else:
            print("   (Function is sync)")
            result = get_price_func("NVDA")
        
        print(f"✅ Success! Result: {result}")
        
    except Exception as e:
        print(f"❌ Error calling get_current_stock_price: {e}")
        print(f"   Error type: {type(e).__name__}")
        
        # Print more detailed error info
        import traceback
        print("\n📋 Full traceback:")
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🔍 Testing other YFinance functions")
    print("=" * 50)
    
    # Test other functions if available
    for tool in yf_tools.tools:
        func_name = getattr(tool, '__name__', 'unknown')
        if func_name != 'get_current_stock_price':
            print(f"\n🧪 Testing {func_name}...")
            try:
                # Try with NVDA as argument
                if inspect.iscoroutinefunction(tool):
                    result = await tool("NVDA")
                else:
                    result = tool("NVDA")
                print(f"✅ {func_name} succeeded: {str(result)[:100]}...")
            except Exception as e:
                print(f"❌ {func_name} failed: {e}")


def test_yfinance_import():
    """Test if we can import yfinance directly."""
    print("\n" + "=" * 50)
    print("📦 Testing direct yfinance import")
    print("=" * 50)
    
    try:
        import yfinance as yf
        print("✅ yfinance imported successfully")
        
        # Test direct yfinance call
        print("🧪 Testing direct yfinance.Ticker('NVDA').info...")
        ticker = yf.Ticker("NVDA")
        info = ticker.info
        
        if info:
            print(f"✅ Direct yfinance call succeeded!")
            print(f"   Company: {info.get('longName', 'N/A')}")
            print(f"   Current Price: ${info.get('currentPrice', 'N/A')}")
            print(f"   Market Cap: {info.get('marketCap', 'N/A')}")
        else:
            print("⚠️  yfinance returned empty info")
            
    except ImportError as e:
        print(f"❌ Cannot import yfinance: {e}")
        print("   You may need to install it: pip install yfinance")
    except Exception as e:
        print(f"❌ Error using yfinance directly: {e}")
        import traceback
        traceback.print_exc()


def check_environment():
    """Check environment and dependencies."""
    print("🔧 Environment Check")
    print("=" * 50)
    
    # Check Python version
    print(f"🐍 Python version: {sys.version}")
    
    # Check if we're in the right directory
    print(f"📁 Current directory: {Path.cwd()}")
    
    # Check if agno is available
    try:
        import agno
        print(f"✅ Agno version: {getattr(agno, '__version__', 'unknown')}")
    except ImportError as e:
        print(f"❌ Cannot import agno: {e}")
    
    # Check if yfinance is available
    try:
        import yfinance
        print(f"✅ yfinance available: {getattr(yfinance, '__version__', 'unknown')}")
    except ImportError as e:
        print(f"❌ yfinance not available: {e}")
    
    # Check internet connectivity
    try:
        import requests
        response = requests.get("https://httpbin.org/status/200", timeout=5)
        if response.status_code == 200:
            print("✅ Internet connectivity: OK")
        else:
            print(f"⚠️  Internet connectivity: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Internet connectivity: {e}")


async def main():
    """Main test function."""
    print("🚀 YFinance Tools Debug Script")
    print("=" * 50)
    
    # Environment check
    check_environment()
    
    # Test direct yfinance
    test_yfinance_import()
    
    # Test Agno YFinance tools
    await test_yfinance_tools()
    
    print("\n" + "=" * 50)
    print("🎉 Debug script completed!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
