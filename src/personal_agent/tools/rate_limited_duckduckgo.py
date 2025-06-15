"""
Rate-limited DuckDuckGo tools to prevent hitting API rate limits.

This module provides a custom implementation of DuckDuckGo search tools
with built-in rate limiting and retry mechanisms to avoid 202 rate limit errors.
"""

import asyncio
import time
from typing import Any, List, Optional

from agno.tools import Toolkit
from agno.utils.log import log_debug
from duckduckgo_search import DDGS

from ..utils import setup_logging

logger = setup_logging(__name__)


class RateLimitedDuckDuckGoTools(Toolkit):
    """
    Rate-limited DuckDuckGo search tools with configurable delays.

    Args:
        search_delay (float): Delay in seconds between search requests (default: 2.0)
        max_retries (int): Maximum number of retries on rate limit (default: 3)
        retry_delay (float): Delay in seconds between retries (default: 5.0)
        enable_text_search (bool): Enable text search functionality
        enable_news_search (bool): Enable news search functionality
        enable_image_search (bool): Enable image search functionality
    """

    def __init__(
        self,
        search_delay: float = 2.0,
        max_retries: int = 3,
        retry_delay: float = 5.0,
        enable_text_search: bool = True,
        enable_news_search: bool = True,
        enable_image_search: bool = False,
        **kwargs,
    ):
        self.search_delay = search_delay
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.last_search_time = 0.0

        tools: List[Any] = []

        if enable_text_search:
            tools.append(self.duckduckgo_search)
        if enable_news_search:
            tools.append(self.duckduckgo_news)
        if enable_image_search:
            tools.append(self.duckduckgo_images)

        super().__init__(name="rate_limited_duckduckgo", tools=tools, **kwargs)
        
        logger.info(
            "Initialized RateLimitedDuckDuckGoTools with search_delay=%.1fs, max_retries=%d, retry_delay=%.1fs",
            search_delay, max_retries, retry_delay
        )

    def _enforce_rate_limit(self) -> None:
        """Enforce rate limiting by waiting if necessary."""
        current_time = time.time()
        time_since_last_search = current_time - self.last_search_time
        
        if time_since_last_search < self.search_delay:
            sleep_time = self.search_delay - time_since_last_search
            logger.debug("Rate limiting: sleeping for %.2f seconds", sleep_time)
            time.sleep(sleep_time)
        
        self.last_search_time = time.time()

    def _search_with_retry(self, search_func, *args, **kwargs) -> Any:
        """Execute a search function with retry logic for rate limits."""
        for attempt in range(self.max_retries + 1):
            try:
                self._enforce_rate_limit()
                result = search_func(*args, **kwargs)
                logger.debug("Search successful on attempt %d", attempt + 1)
                return result
                
            except Exception as e:
                error_str = str(e).lower()
                
                # Check if it's a rate limit error
                if "ratelimit" in error_str or "rate limit" in error_str or "202" in error_str:
                    if attempt < self.max_retries:
                        wait_time = self.retry_delay * (attempt + 1)  # Exponential backoff
                        logger.warning(
                            "Rate limit hit on attempt %d, retrying in %.1f seconds...", 
                            attempt + 1, wait_time
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error("Max retries exceeded for rate limit error: %s", e)
                        return f"❌ Rate limit exceeded after {self.max_retries} retries. Please try again later."
                else:
                    # Non-rate-limit error, don't retry
                    logger.error("Search error (non-rate-limit): %s", e)
                    return f"❌ Search error: {str(e)}"
        
        return "❌ Unexpected error in search retry logic"

    def duckduckgo_search(self, query: str, max_results: int = 5) -> str:
        """Search DuckDuckGo with rate limiting.

        Args:
            query: Search query
            max_results: Maximum number of results to return (default: 5)

        Returns:
            Search results formatted as text or error message
        """
        try:
            logger.info("Performing rate-limited DuckDuckGo search: %s", query)
            
            def search_func():
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=max_results))
                    return results
            
            results = self._search_with_retry(search_func)
            
            if isinstance(results, str):  # Error message
                return results
            
            if not results:
                return f"🔍 No results found for: {query}"
            
            # Format results
            formatted_results = f"🔍 DuckDuckGo search results for '{query}':\n\n"
            
            for i, result in enumerate(results, 1):
                title = result.get('title', 'No title')
                body = result.get('body', 'No description')
                href = result.get('href', 'No URL')
                
                formatted_results += f"{i}. **{title}**\n"
                formatted_results += f"   {body}\n"
                formatted_results += f"   🔗 {href}\n\n"
            
            log_debug(f"DuckDuckGo search completed: {len(results)} results for '{query}'")
            return formatted_results
            
        except Exception as e:
            logger.error("Error in duckduckgo_search: %s", e)
            return f"❌ Search error: {str(e)}"

    def duckduckgo_news(self, query: str, max_results: int = 5) -> str:
        """Search DuckDuckGo news with rate limiting.

        Args:
            query: News search query
            max_results: Maximum number of results to return (default: 5)

        Returns:
            News results formatted as text or error message
        """
        try:
            logger.info("Performing rate-limited DuckDuckGo news search: %s", query)
            
            def search_func():
                with DDGS() as ddgs:
                    results = list(ddgs.news(query, max_results=max_results))
                    return results
            
            results = self._search_with_retry(search_func)
            
            if isinstance(results, str):  # Error message
                return results
            
            if not results:
                return f"📰 No news found for: {query}"
            
            # Format results
            formatted_results = f"📰 DuckDuckGo news results for '{query}':\n\n"
            
            for i, result in enumerate(results, 1):
                title = result.get('title', 'No title')
                body = result.get('body', 'No description')
                url = result.get('url', 'No URL')
                date = result.get('date', 'No date')
                source = result.get('source', 'Unknown source')
                
                formatted_results += f"{i}. **{title}**\n"
                formatted_results += f"   📅 {date} | 📰 {source}\n"
                formatted_results += f"   {body}\n"
                formatted_results += f"   🔗 {url}\n\n"
            
            log_debug(f"DuckDuckGo news search completed: {len(results)} results for '{query}'")
            return formatted_results
            
        except Exception as e:
            logger.error("Error in duckduckgo_news: %s", e)
            return f"❌ News search error: {str(e)}"

    def duckduckgo_images(self, query: str, max_results: int = 5) -> str:
        """Search DuckDuckGo images with rate limiting.

        Args:
            query: Image search query
            max_results: Maximum number of results to return (default: 5)

        Returns:
            Image results formatted as text or error message
        """
        try:
            logger.info("Performing rate-limited DuckDuckGo image search: %s", query)
            
            def search_func():
                with DDGS() as ddgs:
                    results = list(ddgs.images(query, max_results=max_results))
                    return results
            
            results = self._search_with_retry(search_func)
            
            if isinstance(results, str):  # Error message
                return results
            
            if not results:
                return f"🖼️ No images found for: {query}"
            
            # Format results
            formatted_results = f"🖼️ DuckDuckGo image results for '{query}':\n\n"
            
            for i, result in enumerate(results, 1):
                title = result.get('title', 'No title')
                image_url = result.get('image', 'No URL')
                thumbnail = result.get('thumbnail', 'No thumbnail')
                source = result.get('source', 'Unknown source')
                
                formatted_results += f"{i}. **{title}**\n"
                formatted_results += f"   🖼️ {image_url}\n"
                formatted_results += f"   📰 Source: {source}\n\n"
            
            log_debug(f"DuckDuckGo image search completed: {len(results)} results for '{query}'")
            return formatted_results
            
        except Exception as e:
            logger.error("Error in duckduckgo_images: %s", e)
            return f"❌ Image search error: {str(e)}"

    def get_rate_limit_info(self) -> str:
        """Get information about current rate limiting configuration.

        Returns:
            Rate limiting configuration details
        """
        current_time = time.time()
        time_since_last = current_time - self.last_search_time
        
        info = f"⚙️ Rate Limiting Configuration:\n"
        info += f"   • Search delay: {self.search_delay}s between requests\n"
        info += f"   • Max retries: {self.max_retries}\n"
        info += f"   • Retry delay: {self.retry_delay}s (with exponential backoff)\n"
        info += f"   • Time since last search: {time_since_last:.1f}s\n"
        info += f"   • Ready for next search: {'✅ Yes' if time_since_last >= self.search_delay else '⏳ No'}"
        
        return info


# Async version for better integration with async agents
class AsyncRateLimitedDuckDuckGoTools(Toolkit):
    """
    Async rate-limited DuckDuckGo search tools with configurable delays.

    Args:
        search_delay (float): Delay in seconds between search requests (default: 2.0)
        max_retries (int): Maximum number of retries on rate limit (default: 3)
        retry_delay (float): Delay in seconds between retries (default: 5.0)
        enable_text_search (bool): Enable text search functionality
        enable_news_search (bool): Enable news search functionality
        enable_image_search (bool): Enable image search functionality
    """

    def __init__(
        self,
        search_delay: float = 2.0,
        max_retries: int = 3,
        retry_delay: float = 5.0,
        enable_text_search: bool = True,
        enable_news_search: bool = True,
        enable_image_search: bool = False,
        **kwargs,
    ):
        self.search_delay = search_delay
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.last_search_time = 0.0

        tools: List[Any] = []

        if enable_text_search:
            tools.append(self.duckduckgo_search)
        if enable_news_search:
            tools.append(self.duckduckgo_news)
        if enable_image_search:
            tools.append(self.duckduckgo_images)

        super().__init__(name="async_rate_limited_duckduckgo", tools=tools, **kwargs)
        
        logger.info(
            "Initialized AsyncRateLimitedDuckDuckGoTools with search_delay=%.1fs, max_retries=%d, retry_delay=%.1fs",
            search_delay, max_retries, retry_delay
        )

    async def _enforce_rate_limit(self) -> None:
        """Enforce rate limiting by waiting if necessary (async version)."""
        current_time = time.time()
        time_since_last_search = current_time - self.last_search_time
        
        if time_since_last_search < self.search_delay:
            sleep_time = self.search_delay - time_since_last_search
            logger.debug("Rate limiting: sleeping for %.2f seconds", sleep_time)
            await asyncio.sleep(sleep_time)
        
        self.last_search_time = time.time()

    async def _search_with_retry(self, search_func, *args, **kwargs) -> Any:
        """Execute a search function with retry logic for rate limits (async version)."""
        for attempt in range(self.max_retries + 1):
            try:
                await self._enforce_rate_limit()
                # Run the sync search function in a thread pool
                result = await asyncio.get_event_loop().run_in_executor(
                    None, search_func, *args, **kwargs
                )
                logger.debug("Search successful on attempt %d", attempt + 1)
                return result
                
            except Exception as e:
                error_str = str(e).lower()
                
                # Check if it's a rate limit error
                if "ratelimit" in error_str or "rate limit" in error_str or "202" in error_str:
                    if attempt < self.max_retries:
                        wait_time = self.retry_delay * (attempt + 1)  # Exponential backoff
                        logger.warning(
                            "Rate limit hit on attempt %d, retrying in %.1f seconds...", 
                            attempt + 1, wait_time
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.error("Max retries exceeded for rate limit error: %s", e)
                        return f"❌ Rate limit exceeded after {self.max_retries} retries. Please try again later."
                else:
                    # Non-rate-limit error, don't retry
                    logger.error("Search error (non-rate-limit): %s", e)
                    return f"❌ Search error: {str(e)}"
        
        return "❌ Unexpected error in search retry logic"

    async def duckduckgo_search(self, query: str, max_results: int = 5) -> str:
        """Search DuckDuckGo with rate limiting (async version).

        Args:
            query: Search query
            max_results: Maximum number of results to return (default: 5)

        Returns:
            Search results formatted as text or error message
        """
        try:
            logger.info("Performing async rate-limited DuckDuckGo search: %s", query)
            
            def search_func():
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=max_results))
                    return results
            
            results = await self._search_with_retry(search_func)
            
            if isinstance(results, str):  # Error message
                return results
            
            if not results:
                return f"🔍 No results found for: {query}"
            
            # Format results
            formatted_results = f"🔍 DuckDuckGo search results for '{query}':\n\n"
            
            for i, result in enumerate(results, 1):
                title = result.get('title', 'No title')
                body = result.get('body', 'No description')
                href = result.get('href', 'No URL')
                
                formatted_results += f"{i}. **{title}**\n"
                formatted_results += f"   {body}\n"
                formatted_results += f"   🔗 {href}\n\n"
            
            log_debug(f"DuckDuckGo search completed: {len(results)} results for '{query}'")
            return formatted_results
            
        except Exception as e:
            logger.error("Error in async duckduckgo_search: %s", e)
            return f"❌ Search error: {str(e)}"

    async def duckduckgo_news(self, query: str, max_results: int = 5) -> str:
        """Search DuckDuckGo news with rate limiting (async version).

        Args:
            query: News search query
            max_results: Maximum number of results to return (default: 5)

        Returns:
            News results formatted as text or error message
        """
        try:
            logger.info("Performing async rate-limited DuckDuckGo news search: %s", query)
            
            def search_func():
                with DDGS() as ddgs:
                    results = list(ddgs.news(query, max_results=max_results))
                    return results
            
            results = await self._search_with_retry(search_func)
            
            if isinstance(results, str):  # Error message
                return results
            
            if not results:
                return f"📰 No news found for: {query}"
            
            # Format results
            formatted_results = f"📰 DuckDuckGo news results for '{query}':\n\n"
            
            for i, result in enumerate(results, 1):
                title = result.get('title', 'No title')
                body = result.get('body', 'No description')
                url = result.get('url', 'No URL')
                date = result.get('date', 'No date')
                source = result.get('source', 'Unknown source')
                
                formatted_results += f"{i}. **{title}**\n"
                formatted_results += f"   📅 {date} | 📰 {source}\n"
                formatted_results += f"   {body}\n"
                formatted_results += f"   🔗 {url}\n\n"
            
            log_debug(f"DuckDuckGo news search completed: {len(results)} results for '{query}'")
            return formatted_results
            
        except Exception as e:
            logger.error("Error in async duckduckgo_news: %s", e)
            return f"❌ News search error: {str(e)}"

    async def duckduckgo_images(self, query: str, max_results: int = 5) -> str:
        """Search DuckDuckGo images with rate limiting (async version).

        Args:
            query: Image search query
            max_results: Maximum number of results to return (default: 5)

        Returns:
            Image results formatted as text or error message
        """
        try:
            logger.info("Performing async rate-limited DuckDuckGo image search: %s", query)
            
            def search_func():
                with DDGS() as ddgs:
                    results = list(ddgs.images(query, max_results=max_results))
                    return results
            
            results = await self._search_with_retry(search_func)
            
            if isinstance(results, str):  # Error message
                return results
            
            if not results:
                return f"🖼️ No images found for: {query}"
            
            # Format results
            formatted_results = f"🖼️ DuckDuckGo image results for '{query}':\n\n"
            
            for i, result in enumerate(results, 1):
                title = result.get('title', 'No title')
                image_url = result.get('image', 'No URL')
                thumbnail = result.get('thumbnail', 'No thumbnail')
                source = result.get('source', 'Unknown source')
                
                formatted_results += f"{i}. **{title}**\n"
                formatted_results += f"   🖼️ {image_url}\n"
                formatted_results += f"   📰 Source: {source}\n\n"
            
            log_debug(f"DuckDuckGo image search completed: {len(results)} results for '{query}'")
            return formatted_results
            
        except Exception as e:
            logger.error("Error in async duckduckgo_images: %s", e)
            return f"❌ Image search error: {str(e)}"
