"""
Knowledge Coordinator for Personal AI Agent

This module provides a unified interface for querying both local semantic knowledge
and LightRAG graph-based knowledge systems. It intelligently routes queries based
on mode parameters and query characteristics.
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Tuple, Union

import aiohttp

from ..config.settings import LIGHTRAG_URL
from ..utils import setup_logging

logger = setup_logging(__name__)


class KnowledgeCoordinator:
    """
    Coordinates queries between local semantic search and LightRAG graph systems.
    
    This class implements the Knowledge Coordinator shown in the architecture diagram,
    providing intelligent routing based on mode parameters and query analysis.
    """

    def __init__(
        self,
        agno_knowledge=None,
        lightrag_url: str = LIGHTRAG_URL,
        debug: bool = False
    ):
        """
        Initialize the Knowledge Coordinator.
        
        Args:
            agno_knowledge: Local semantic knowledge base (SQLite/LanceDB)
            lightrag_url: URL for LightRAG server
            debug: Enable debug logging
        """
        self.agno_knowledge = agno_knowledge
        self.lightrag_url = lightrag_url
        self.debug = debug
        
        # Query routing statistics
        self.routing_stats = {
            "local_semantic": 0,
            "lightrag": 0,
            "auto_detected_local": 0,
            "auto_detected_lightrag": 0,
            "fallback_used": 0
        }
        
        logger.info("Knowledge Coordinator initialized with LightRAG URL: %s", lightrag_url)

    def _is_simple_fact_query(self, query: str) -> bool:
        """
        Determine if a query is a simple fact lookup suitable for local semantic search.
        
        Args:
            query: The search query
            
        Returns:
            True if query appears to be a simple fact lookup
        """
        query_lower = query.lower().strip()
        
        # Simple fact indicators
        simple_patterns = [
            r'^what is\s+\w+',  # "what is X"
            r'^who is\s+\w+',   # "who is X"
            r'^when did\s+\w+', # "when did X"
            r'^where is\s+\w+', # "where is X"
            r'^how much\s+\w+', # "how much X"
            r'^define\s+\w+',   # "define X"
            r'^\w+\s+definition', # "X definition"
        ]
        
        for pattern in simple_patterns:
            if re.match(pattern, query_lower):
                return True
                
        # Short queries are often simple facts
        if len(query.split()) <= 3:
            return True
            
        return False

    def _has_relationship_keywords(self, query: str) -> bool:
        """
        Determine if a query involves relationships suitable for graph search.
        
        Args:
            query: The search query
            
        Returns:
            True if query appears to involve relationships or complex analysis
        """
        query_lower = query.lower()
        
        # Relationship indicators
        relationship_keywords = [
            'relationship', 'connection', 'related', 'linked', 'associated',
            'compare', 'contrast', 'difference', 'similarity', 'versus',
            'how does', 'why does', 'what causes', 'impact of', 'effect of',
            'analyze', 'analysis', 'explain', 'reasoning', 'because',
            'correlation', 'influence', 'affect', 'consequence', 'result',
            'pattern', 'trend', 'network', 'graph', 'hierarchy'
        ]
        
        for keyword in relationship_keywords:
            if keyword in query_lower:
                return True
                
        # Complex question patterns
        complex_patterns = [
            r'how\s+\w+\s+\w+\s+\w+',  # "how X Y Z" (longer how questions)
            r'why\s+\w+\s+\w+',        # "why X Y"
            r'what\s+causes?\s+\w+',   # "what causes X"
            r'explain\s+\w+',          # "explain X"
        ]
        
        for pattern in complex_patterns:
            if re.search(pattern, query_lower):
                return True
                
        return False

    def _determine_routing(self, query: str, mode: str) -> Tuple[str, str]:
        """
        Determine which knowledge system to use based on mode and query analysis.
        
        Args:
            query: The search query
            mode: Routing mode specification
            
        Returns:
            Tuple of (routing_decision, reasoning)
        """
        mode_lower = mode.lower().strip()
        
        # Explicit mode routing
        if mode_lower == "local":
            return "local_semantic", f"Explicit mode=local routing"
            
        if mode_lower in ["global", "hybrid", "mix", "naive", "bypass"]:
            return "lightrag", f"Explicit mode={mode_lower} routing to LightRAG"
            
        # Auto-detection for mode="auto" or unspecified
        if mode_lower in ["auto", "", "none"]:
            if self._is_simple_fact_query(query):
                self.routing_stats["auto_detected_local"] += 1
                return "local_semantic", "Auto-detected: Simple fact query → Local semantic"
                
            if self._has_relationship_keywords(query):
                self.routing_stats["auto_detected_lightrag"] += 1
                return "lightrag", "Auto-detected: Relationship query → LightRAG"
                
            # Default to local for speed
            self.routing_stats["auto_detected_local"] += 1
            return "local_semantic", "Auto-detected: Default to local semantic for speed"
            
        # Unknown mode - default to local
        logger.warning("Unknown mode '%s', defaulting to local semantic", mode)
        return "local_semantic", f"Unknown mode '{mode}' → Default to local semantic"

    async def _query_local_semantic(
        self, 
        query: str, 
        limit: int = 5
    ) -> str:
        """
        Query the local semantic knowledge base (SQLite/LanceDB).
        
        Args:
            query: The search query
            limit: Maximum number of results
            
        Returns:
            Formatted search results
        """
        if not self.agno_knowledge:
            return "❌ Local semantic knowledge base is not available."
            
        try:
            results = self.agno_knowledge.search(query=query, num_documents=limit)
            
            if not results:
                return f"🔍 No results found in local knowledge base for '{query}'."
                
            # Format results
            formatted_results = []
            for i, result in enumerate(results, 1):
                source_info = f"(Source: {result.source})" if hasattr(result, 'source') and result.source else ""
                formatted_results.append(f"**Result {i}** {source_info}\n{result.content}")
                
            response = f"📚 **Local Knowledge Search Results** for '{query}':\n\n"
            response += "\n\n".join(formatted_results)
            
            logger.info("Local semantic search returned %d results for: %s", len(results), query)
            return response
            
        except Exception as e:
            logger.error("Error in local semantic search: %s", e)
            return f"❌ Error searching local knowledge base: {str(e)}"

    async def _query_lightrag(
        self,
        query: str,
        mode: str = "hybrid",
        top_k: int = 5,
        response_type: str = "Multiple Paragraphs"
    ) -> str:
        """
        Query the LightRAG graph knowledge system.
        
        Args:
            query: The search query
            mode: LightRAG query mode
            top_k: Number of top results
            response_type: Response format
            
        Returns:
            LightRAG response content
        """
        try:
            url = f"{self.lightrag_url}/query"
            payload = {
                "query": query,
                "mode": mode,
                "top_k": top_k,
                "response_type": response_type,
            }
            
            logger.debug("Querying LightRAG: %s with payload: %s", url, payload)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=120) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.error("LightRAG server error %d: %s", resp.status, error_text)
                        return f"❌ LightRAG server error {resp.status}: {error_text}"
                        
                    result = await resp.json()
                    
                    # Extract response content
                    if isinstance(result, dict) and "response" in result:
                        response_content = result["response"]
                    elif isinstance(result, dict) and "content" in result:
                        response_content = result["content"]
                    elif isinstance(result, dict) and "answer" in result:
                        response_content = result["answer"]
                    else:
                        response_content = str(result)
                        
                    # Add header to indicate source
                    formatted_response = f"🌐 **LightRAG Knowledge Graph Results** (mode: {mode}) for '{query}':\n\n{response_content}"
                    
                    logger.info("LightRAG search completed for: %s", query)
                    return formatted_response
                    
        except aiohttp.ClientConnectorError as e:
            error_msg = f"❌ Cannot connect to LightRAG server at {self.lightrag_url}. Is the server running? Error: {str(e)}"
            logger.error(error_msg)
            return error_msg
        except asyncio.TimeoutError as e:
            error_msg = f"❌ Timeout connecting to LightRAG server at {self.lightrag_url}. Error: {str(e)}"
            logger.error(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"❌ Error querying LightRAG: {str(e)}"
            logger.error(error_msg)
            return error_msg

    async def query_knowledge_base(
        self,
        query: str,
        mode: str = "auto",
        limit: int = 5,
        response_type: str = "Multiple Paragraphs"
    ) -> str:
        """
        Unified knowledge base query with intelligent routing.
        
        This is the main entry point for all knowledge queries. It intelligently
        routes queries between local semantic search and LightRAG based on the
        mode parameter and query characteristics.
        
        Args:
            query: The search query
            mode: Routing mode:
                  - "local": Force local semantic search
                  - "global", "hybrid", "mix", "naive", "bypass": Use LightRAG
                  - "auto": Intelligent auto-detection (default)
            limit: Maximum results for local search / top_k for LightRAG
            response_type: Format for LightRAG responses
            
        Returns:
            Formatted search results from the appropriate knowledge system
        """
        if not query or not query.strip():
            return "❌ Error: Query cannot be empty. Please provide a search term."
            
        query = query.strip()
        
        # Determine routing
        routing_decision, reasoning = self._determine_routing(query, mode)
        
        if self.debug:
            logger.info("Knowledge routing: %s (%s)", routing_decision, reasoning)
            
        # Update statistics
        self.routing_stats[routing_decision] += 1
        
        # Route to appropriate system
        try:
            if routing_decision == "local_semantic":
                result = await self._query_local_semantic(query, limit)
                
                # If local search fails and we have LightRAG available, try fallback
                if result.startswith("❌") and self.lightrag_url:
                    logger.info("Local search failed, attempting LightRAG fallback")
                    self.routing_stats["fallback_used"] += 1
                    fallback_result = await self._query_lightrag(query, "hybrid", limit, response_type)
                    return f"{result}\n\n**Fallback to LightRAG:**\n{fallback_result}"
                    
                return result
                
            elif routing_decision == "lightrag":
                # For LightRAG, use the original mode if it was explicitly specified
                lightrag_mode = mode if mode.lower() in ["global", "hybrid", "mix", "naive", "bypass"] else "hybrid"
                result = await self._query_lightrag(query, lightrag_mode, limit, response_type)
                
                # If LightRAG fails and we have local knowledge, try fallback
                if result.startswith("❌") and self.agno_knowledge:
                    logger.info("LightRAG failed, attempting local semantic fallback")
                    self.routing_stats["fallback_used"] += 1
                    fallback_result = await self._query_local_semantic(query, limit)
                    return f"{result}\n\n**Fallback to Local Search:**\n{fallback_result}"
                    
                return result
                
            else:
                return f"❌ Unknown routing decision: {routing_decision}"
                
        except Exception as e:
            logger.error("Error in knowledge coordinator: %s", e)
            return f"❌ Error processing knowledge query: {str(e)}"

    def get_routing_stats(self) -> Dict[str, Union[int, float]]:
        """
        Get statistics about query routing decisions.
        
        Returns:
            Dictionary with routing statistics
        """
        total_queries = sum(self.routing_stats.values())
        
        if total_queries == 0:
            return {"total_queries": 0, "message": "No queries processed yet"}
            
        stats = self.routing_stats.copy()
        stats["total_queries"] = total_queries
        
        # Add percentages
        for key, value in self.routing_stats.items():
            stats[f"{key}_percentage"] = (value / total_queries) * 100
            
        return stats

    def reset_stats(self) -> None:
        """Reset routing statistics."""
        self.routing_stats = {
            "local_semantic": 0,
            "lightrag": 0,
            "auto_detected_local": 0,
            "auto_detected_lightrag": 0,
            "fallback_used": 0
        }
        logger.info("Knowledge coordinator statistics reset")


# Convenience function for creating a knowledge coordinator
def create_knowledge_coordinator(
    agno_knowledge=None,
    lightrag_url: str = LIGHTRAG_URL,
    debug: bool = False
) -> KnowledgeCoordinator:
    """
    Create a Knowledge Coordinator instance.
    
    Args:
        agno_knowledge: Local semantic knowledge base
        lightrag_url: URL for LightRAG server
        debug: Enable debug logging
        
    Returns:
        Configured KnowledgeCoordinator instance
    """
    return KnowledgeCoordinator(
        agno_knowledge=agno_knowledge,
        lightrag_url=lightrag_url,
        debug=debug
    )
