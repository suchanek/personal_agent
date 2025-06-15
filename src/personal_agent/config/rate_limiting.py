"""
Rate limiting configuration for Personal Agent tools.

This module provides centralized configuration for rate limiting settings
across different tools and services to prevent hitting API rate limits.
"""

import os
from typing import Dict, Any


class RateLimitConfig:
    """Configuration class for rate limiting settings."""
    
    # DuckDuckGo Search Rate Limiting
    DUCKDUCKGO_SEARCH_DELAY = float(os.getenv("DUCKDUCKGO_SEARCH_DELAY", "3.0"))  # seconds between searches
    DUCKDUCKGO_MAX_RETRIES = int(os.getenv("DUCKDUCKGO_MAX_RETRIES", "3"))        # max retries on rate limit
    DUCKDUCKGO_RETRY_DELAY = float(os.getenv("DUCKDUCKGO_RETRY_DELAY", "10.0"))   # base retry delay (exponential backoff)
    
    # General API Rate Limiting
    DEFAULT_API_DELAY = float(os.getenv("DEFAULT_API_DELAY", "1.0"))              # default delay between API calls
    DEFAULT_MAX_RETRIES = int(os.getenv("DEFAULT_MAX_RETRIES", "3"))              # default max retries
    DEFAULT_RETRY_DELAY = float(os.getenv("DEFAULT_RETRY_DELAY", "5.0"))          # default retry delay
    
    # Tool-specific rate limiting (can be extended for other tools)
    TOOL_RATE_LIMITS = {
        "duckduckgo": {
            "search_delay": DUCKDUCKGO_SEARCH_DELAY,
            "max_retries": DUCKDUCKGO_MAX_RETRIES,
            "retry_delay": DUCKDUCKGO_RETRY_DELAY,
        },
        "default": {
            "search_delay": DEFAULT_API_DELAY,
            "max_retries": DEFAULT_MAX_RETRIES,
            "retry_delay": DEFAULT_RETRY_DELAY,
        }
    }
    
    @classmethod
    def get_tool_config(cls, tool_name: str) -> Dict[str, Any]:
        """Get rate limiting configuration for a specific tool.
        
        Args:
            tool_name: Name of the tool (e.g., 'duckduckgo', 'github', etc.)
            
        Returns:
            Dictionary containing rate limiting configuration
        """
        return cls.TOOL_RATE_LIMITS.get(tool_name, cls.TOOL_RATE_LIMITS["default"])
    
    @classmethod
    def update_tool_config(cls, tool_name: str, **kwargs) -> None:
        """Update rate limiting configuration for a specific tool.
        
        Args:
            tool_name: Name of the tool
            **kwargs: Configuration parameters to update
        """
        if tool_name not in cls.TOOL_RATE_LIMITS:
            cls.TOOL_RATE_LIMITS[tool_name] = cls.TOOL_RATE_LIMITS["default"].copy()
        
        cls.TOOL_RATE_LIMITS[tool_name].update(kwargs)
    
    @classmethod
    def get_duckduckgo_config(cls) -> Dict[str, Any]:
        """Get DuckDuckGo-specific rate limiting configuration.
        
        Returns:
            Dictionary with DuckDuckGo rate limiting settings
        """
        return cls.get_tool_config("duckduckgo")
    
    @classmethod
    def print_config(cls) -> str:
        """Print current rate limiting configuration.
        
        Returns:
            Formatted string showing current configuration
        """
        config_str = "⚙️ Rate Limiting Configuration:\n"
        config_str += "=" * 40 + "\n"
        
        for tool_name, config in cls.TOOL_RATE_LIMITS.items():
            config_str += f"\n🔧 {tool_name.upper()}:\n"
            config_str += f"   • Search delay: {config['search_delay']}s\n"
            config_str += f"   • Max retries: {config['max_retries']}\n"
            config_str += f"   • Retry delay: {config['retry_delay']}s\n"
        
        config_str += "\n💡 Environment Variables:\n"
        config_str += f"   • DUCKDUCKGO_SEARCH_DELAY={cls.DUCKDUCKGO_SEARCH_DELAY}\n"
        config_str += f"   • DUCKDUCKGO_MAX_RETRIES={cls.DUCKDUCKGO_MAX_RETRIES}\n"
        config_str += f"   • DUCKDUCKGO_RETRY_DELAY={cls.DUCKDUCKGO_RETRY_DELAY}\n"
        config_str += f"   • DEFAULT_API_DELAY={cls.DEFAULT_API_DELAY}\n"
        config_str += f"   • DEFAULT_MAX_RETRIES={cls.DEFAULT_MAX_RETRIES}\n"
        config_str += f"   • DEFAULT_RETRY_DELAY={cls.DEFAULT_RETRY_DELAY}\n"
        
        return config_str


# Convenience functions for common operations
def get_duckduckgo_rate_limits() -> Dict[str, Any]:
    """Get DuckDuckGo rate limiting configuration.
    
    Returns:
        Dictionary with rate limiting settings for DuckDuckGo
    """
    return RateLimitConfig.get_duckduckgo_config()


def set_duckduckgo_rate_limits(search_delay: float = None, max_retries: int = None, retry_delay: float = None) -> None:
    """Set DuckDuckGo rate limiting configuration.
    
    Args:
        search_delay: Delay in seconds between searches
        max_retries: Maximum number of retries on rate limit
        retry_delay: Base delay for retries (with exponential backoff)
    """
    updates = {}
    if search_delay is not None:
        updates["search_delay"] = search_delay
    if max_retries is not None:
        updates["max_retries"] = max_retries
    if retry_delay is not None:
        updates["retry_delay"] = retry_delay
    
    if updates:
        RateLimitConfig.update_tool_config("duckduckgo", **updates)


def print_rate_limit_config() -> None:
    """Print the current rate limiting configuration."""
    print(RateLimitConfig.print_config())


# Preset configurations for different use cases
RATE_LIMIT_PRESETS = {
    "conservative": {
        "search_delay": 5.0,
        "max_retries": 2,
        "retry_delay": 15.0,
    },
    "balanced": {
        "search_delay": 3.0,
        "max_retries": 3,
        "retry_delay": 10.0,
    },
    "aggressive": {
        "search_delay": 1.0,
        "max_retries": 5,
        "retry_delay": 5.0,
    },
    "development": {
        "search_delay": 0.5,
        "max_retries": 1,
        "retry_delay": 2.0,
    }
}


def apply_rate_limit_preset(preset_name: str, tool_name: str = "duckduckgo") -> bool:
    """Apply a preset rate limiting configuration.
    
    Args:
        preset_name: Name of the preset ('conservative', 'balanced', 'aggressive', 'development')
        tool_name: Name of the tool to apply the preset to
        
    Returns:
        True if preset was applied successfully, False otherwise
    """
    if preset_name not in RATE_LIMIT_PRESETS:
        print(f"❌ Unknown preset: {preset_name}")
        print(f"Available presets: {', '.join(RATE_LIMIT_PRESETS.keys())}")
        return False
    
    preset_config = RATE_LIMIT_PRESETS[preset_name]
    RateLimitConfig.update_tool_config(tool_name, **preset_config)
    
    print(f"✅ Applied '{preset_name}' preset to {tool_name}")
    print(f"   • Search delay: {preset_config['search_delay']}s")
    print(f"   • Max retries: {preset_config['max_retries']}")
    print(f"   • Retry delay: {preset_config['retry_delay']}s")
    
    return True


if __name__ == "__main__":
    # Demo the configuration system
    print("🚀 Rate Limiting Configuration Demo")
    print()
    
    # Show current configuration
    print_rate_limit_config()
    
    print("\n" + "="*50)
    print("📋 Available Presets:")
    for preset_name, config in RATE_LIMIT_PRESETS.items():
        print(f"\n🎯 {preset_name.upper()}:")
        for key, value in config.items():
            print(f"   • {key}: {value}")
    
    print("\n" + "="*50)
    print("🧪 Testing Preset Application:")
    
    # Test applying a preset
    apply_rate_limit_preset("conservative")
    
    print("\n📊 Updated Configuration:")
    print(RateLimitConfig.print_config())
