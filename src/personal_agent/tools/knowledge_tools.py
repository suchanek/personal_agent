# src/personal_agent/tools/knowledge_tools.py
# pylint: disable=C0301, W1203
"""Dual Knowledge Base Management Tools Module.

This module provides comprehensive tools for managing two complementary knowledge base systems:
a LightRAG-based graph knowledge base and a local semantic vector knowledge base. It enables
intelligent storage, processing, and retrieval of factual information, documents, and reference
materials through multiple search strategies and knowledge representation approaches.

Key Components:
    KnowledgeTools: Main toolkit class providing dual knowledge base operations

Dual Architecture:
    1. LightRAG Knowledge Base (Graph-based):
       - Remote server-based processing via HTTP API
       - Knowledge graph construction with entity relationships
       - Global graph queries and local semantic search
       - Hybrid search combining multiple retrieval strategies
       - Files stored in AGNO_KNOWLEDGE_DIR and uploaded to server

    2. Semantic Knowledge Base (Vector-based):
       - Local LanceDB/Agno-based vector storage
       - Direct vector similarity search
       - Files stored in DATA_DIR/knowledge directory
       - Immediate vector embedding and indexing

Core Functionality:
    - Document ingestion from multiple sources (files, URLs, direct text)
    - Intelligent content processing and metadata extraction
    - Multi-modal search with semantic and graph-based retrieval
    - Batch processing capabilities for large document collections
    - Automatic content validation and error handling
    - Unified querying through KnowledgeCoordinator

Available Methods:
    Unified Operations (Recommended):
    - ingest_file: Upload files to both LightRAG and semantic knowledge bases
    - ingest_text: Upload text content to both LightRAG and semantic knowledge bases
    - ingest_url: Fetch and upload URL content to both LightRAG and semantic knowledge bases
    - query_knowledge_base: Unified querying across both knowledge bases

    Individual LightRAG Operations:
    - ingest_knowledge_file: Upload files to LightRAG server only
    - ingest_knowledge_text: Upload text content to LightRAG server only
    - ingest_knowledge_from_url: Fetch and upload URL content to LightRAG only
    - batch_ingest_directory: Batch upload directory contents to LightRAG only
    - query_lightrag_knowledge_direct: Direct LightRAG server queries

    Individual Semantic Operations:
    - ingest_semantic_file: Add files to local semantic knowledge base only
    - ingest_semantic_text: Add text content to local semantic knowledge base only
    - ingest_semantic_from_url: Fetch and add URL content to semantic knowledge base only
    - batch_ingest_semantic_directory: Batch add directory contents to semantic KB only
    - query_semantic_knowledge: Direct semantic vector search
    - recreate_semantic_kb: Rebuild semantic knowledge base indices

Supported Content Types:
    - Text documents (.txt, .md, .csv)
    - PDF documents (.pdf)
    - Microsoft Word documents (.doc, .docx)
    - HTML content (.html)
    - JSON structured data (.json)
    - Web pages and APIs via URL ingestion

Search Capabilities:
    LightRAG Search Modes:
    - Local: Semantic similarity within document chunks
    - Global: Graph-based entity relationship queries
    - Hybrid: Combined semantic and graph approaches
    - Auto-routing: Intelligent query mode selection

    Semantic Search:
    - Vector similarity search using embeddings
    - Direct document retrieval with relevance scoring
    - Configurable result limits and filtering

Usage Patterns:
    This module is designed for storing and retrieving static factual information
    that doesn't change frequently. It's ideal for:
    - Research document repositories
    - Technical documentation systems
    - Reference material collections
    - Knowledge base construction from multiple sources
    - Comparative search across different knowledge representations

    It should NOT be used for:
    - Personal user information (use memory tools instead)
    - Temporary or frequently changing data
    - Creative content generation
    - General conversational AI without knowledge context

Integration:
    - LightRAG: Requires LightRAG server running at configured endpoint
    - Semantic: Uses local Agno knowledge base for vector operations
    - Coordinates with KnowledgeManager and KnowledgeCoordinator
    - Supports both synchronous and asynchronous operations
    - Provides comprehensive logging and error reporting

Performance Considerations:
    - File size limits: 50MB per individual file
    - Batch processing: Maximum 50 files per operation
    - Rate limiting: Built-in delays to prevent server overload
    - Timeout handling: 60-second limits for network operations
    - Unique naming: Automatic conflict resolution for duplicate files
    - Semantic KB: Automatic vector embedding regeneration on ingestion

Dependencies:
    - LightRAG server for graph-based knowledge processing
    - Agno/LanceDB for local semantic vector storage
    - requests/aiohttp for HTTP communication
    - BeautifulSoup for HTML content extraction
    - Standard library modules for file handling and validation

Example Usage:
    ```python
    from personal_agent.tools.knowledge_tools import KnowledgeTools
    from personal_agent.core.knowledge_manager import KnowledgeManager

    # Initialize the tools
    km = KnowledgeManager()
    tools = KnowledgeTools(km, agno_knowledge=agno_kb)

    # Ingest into LightRAG knowledge base
    result = tools.ingest_knowledge_file("research_paper.pdf", "AI Research")

    # Ingest into semantic knowledge base
    result = tools.ingest_semantic_file("reference.txt", "Reference Material")

    # Unified query across both knowledge bases
    answer = tools.query_knowledge_base("What is machine learning?")

    # Direct semantic search
    semantic_results = tools.query_semantic_knowledge("neural networks")

    # Batch process directories
    lightrag_summary = tools.batch_ingest_directory("./docs", "*.pdf")
    semantic_summary = tools.batch_ingest_semantic_directory("./refs", "*.md")
    ```

Author: Personal Agent Development Team
Version: Compatible with LightRAG backend and Agno semantic knowledge base
License: See project LICENSE file
Last revision: 2025-08-14 10:57:57
"""
import hashlib
import mimetypes
import os
import shutil
import time
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import urlparse

import aiohttp
import requests
from agno.tools import Toolkit
from agno.utils.log import log_debug
from bs4 import BeautifulSoup

from ..config import settings
from ..core.knowledge_coordinator import create_knowledge_coordinator
from ..core.knowledge_manager import KnowledgeManager
from ..utils import setup_logging

logger = setup_logging(__name__)


class KnowledgeTools(Toolkit):
    """Knowledge Base Management Tools for Factual Information Storage and Retrieval.
    Use these tools when you need to:
    - Store factual information, documents, or reference materials for future retrieval
    - Search for previously stored knowledge, facts, or documents
    - Ingest content from files, URLs, or text into the knowledge base
    - Find information that was previously added to the knowledge base

    DO NOT use these tools for:
    - Storing personal information about the user (use memory tools instead)
    - Creative requests like writing stories or poems
    - General questions that don't require stored knowledge

    The knowledge base is separate from memory - it's for factual information that doesn't change,
    while memory is for personal information about the user that evolves over time.

    """

    def __init__(self, knowledge_manager: KnowledgeManager, agno_knowledge=None):
        self.knowledge_manager = knowledge_manager
        self.agno_knowledge = agno_knowledge

        # Initialize knowledge coordinator for unified querying
        self.knowledge_coordinator = None

        # Collect knowledge tool methods - now includes unified and individual methods
        tools = [
            # Unified methods (recommended)
            self.ingest_file,
            self.ingest_text,
            self.ingest_url,
            self.batch_ingest_directory,
            self.recreate_semantic_kb,
            # Unified query method
            self.query_knowledge_base,
        ]

        # Initialize the Toolkit
        super().__init__(
            name="persag_knowledge_tools",
            tools=tools,
            instructions="""Use these tools to manage factual information and documents in both knowledge bases.
            Store reference materials, facts, and documents that don't change.
            Query when you need to find previously stored factual information.
            Supports both LightRAG (graph-based) and semantic (vector-based) knowledge bases.
            Do NOT use for personal user information - use memory tools for that.""",
        )

    def ingest_knowledge_file(self, file_path: str, title: str = None) -> str:
        """Ingest a file into the knowledge base.

        Args:
            file_path: Path to the file to ingest
            title: Optional title for the knowledge entry (defaults to filename)

        Returns:
            Success message or error details.
        """
        try:
            # Expand path shortcuts
            if file_path.startswith("~/"):
                file_path = os.path.expanduser(file_path)
            elif file_path.startswith("./"):
                file_path = os.path.abspath(file_path)

            # Validate file exists
            if not os.path.exists(file_path):
                return f"❌ Error: File not found at '{file_path}'"

            if not os.path.isfile(file_path):
                return f"❌ Error: '{file_path}' is not a file"

            # Get file info
            file_size = os.path.getsize(file_path)
            if file_size > 50 * 1024 * 1024:  # 50MB limit
                return f"❌ Error: File too large ({file_size / (1024*1024):.1f}MB). Maximum size is 50MB."

            filename = os.path.basename(file_path)
            if not title:
                title = os.path.splitext(filename)[0]

            # Check file type
            mime_type, _ = mimetypes.guess_type(file_path)
            supported_types = [
                "text/plain",
                "text/markdown",
                "text/html",
                "text/csv",
                "application/pdf",
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ]

            if mime_type and mime_type not in supported_types:
                logger.warning(f"File type {mime_type} may not be fully supported")

            # Copy file to knowledge directory
            knowledge_dir = Path(settings.AGNO_KNOWLEDGE_DIR)
            knowledge_dir.mkdir(parents=True, exist_ok=True)

            # Create unique filename to avoid conflicts
            timestamp = int(time.time())
            file_hash = hashlib.md5(f"{filename}_{timestamp}".encode()).hexdigest()[:8]
            base_name, ext = os.path.splitext(filename)
            unique_filename = f"{base_name}_{file_hash}{ext}"

            dest_path = knowledge_dir / unique_filename

            # Copy the file
            shutil.copy2(file_path, dest_path)
            log_debug(f"Copied file to knowledge directory: {dest_path}")

            # Upload to LightRAG server
            upload_result = self._upload_to_lightrag(
                dest_path, unique_filename, settings.LIGHTRAG_URL
            )

            if "✅" in upload_result:
                logger.info(f"Successfully ingested knowledge file: {filename}")
                return f"✅ Successfully ingested '{filename}' into knowledge base. {upload_result}"
            else:
                # Clean up the copied file if upload failed
                try:
                    os.remove(dest_path)
                except OSError:
                    pass
                return f"❌ Failed to ingest '{filename}': {upload_result}"

        except Exception as e:
            logger.error(f"Error ingesting file {file_path}: {e}")
            return f"❌ Error ingesting file: {str(e)}"

    def ingest_knowledge_text(
        self, content: str, title: str, file_type: str = "txt"
    ) -> str:
        """Ingest text content directly into the knowledge base.

        Args:
            content: The text content to ingest
            title: Title for the knowledge entry
            file_type: File extension to use (txt, md, html, etc.)

        Returns:
            Success message or error details.
        """
        try:
            if not content or not content.strip():
                return "❌ Error: Content cannot be empty"

            if not title or not title.strip():
                return "❌ Error: Title is required"

            # Validate file_type
            if not file_type.startswith("."):
                file_type = f".{file_type}"

            allowed_types = [".txt", ".md", ".html", ".csv", ".json"]
            if file_type not in allowed_types:
                file_type = ".txt"  # Default to txt

            # Create knowledge directory
            knowledge_dir = Path(settings.AGNO_KNOWLEDGE_DIR)
            knowledge_dir.mkdir(parents=True, exist_ok=True)

            # Create unique filename
            timestamp = int(time.time())
            content_hash = hashlib.md5(
                f"{title}_{content[:100]}_{timestamp}".encode()
            ).hexdigest()[:8]
            safe_title = "".join(
                c for c in title if c.isalnum() or c in (" ", "-", "_")
            ).rstrip()
            safe_title = safe_title.replace(" ", "_")[:50]  # Limit length
            filename = f"{safe_title}_{content_hash}{file_type}"

            file_path = knowledge_dir / filename

            # Write content to file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            log_debug(f"Created knowledge file: {file_path}")

            # Upload to LightRAG server
            upload_result = self._upload_to_lightrag(
                file_path, filename, settings.LIGHTRAG_URL
            )

            if "✅" in upload_result:
                logger.info(f"Successfully ingested knowledge text: {title}")
                return f"✅ Successfully ingested '{title}' into knowledge base. {upload_result}"
            else:
                # Clean up the created file if upload failed
                try:
                    os.remove(file_path)
                except OSError:
                    pass
                return f"❌ Failed to ingest '{title}': {upload_result}"

        except Exception as e:
            logger.error(f"Error ingesting text content: {e}")
            return f"❌ Error ingesting text content: {str(e)}"

    def ingest_knowledge_from_url(self, url: str, title: str = None) -> str:
        """Ingest content from a URL into the knowledge base.

        Args:
            url: URL to fetch content from
            title: Optional title for the knowledge entry (defaults to page title or URL)

        Returns:
            Success message or error details.
        """
        try:
            # Validate URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                return f"❌ Error: Invalid URL format: {url}"

            # Fetch content
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }

            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "").lower()

            # Handle different content types
            if "text/html" in content_type:
                # For HTML, try to extract text content
                try:

                    soup = BeautifulSoup(response.content, "html.parser")

                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.decompose()

                    # Get text content
                    content = soup.get_text()

                    # Get title if not provided
                    if not title:
                        title_tag = soup.find("title")
                        title = (
                            title_tag.get_text().strip()
                            if title_tag
                            else parsed_url.netloc
                        )

                    file_type = "html"

                except ImportError:
                    # Fallback if BeautifulSoup not available
                    content = response.text
                    title = title or parsed_url.netloc
                    file_type = "html"

            elif "text/" in content_type or "application/json" in content_type:
                content = response.text
                title = title or parsed_url.netloc
                file_type = "txt" if "text/" in content_type else "json"
            else:
                return f"❌ Error: Unsupported content type: {content_type}"

            # Clean up content
            content = "\n".join(
                line.strip() for line in content.splitlines() if line.strip()
            )

            if not content:
                return f"❌ Error: No content extracted from URL: {url}"

            # Add source URL to content
            content = f"Source: {url}\n\n{content}"

            # Ingest the content
            return self.ingest_knowledge_text(content, title, file_type)

        except requests.RequestException as e:
            logger.error(f"Error fetching URL {url}: {e}")
            return f"❌ Error fetching URL: {str(e)}"
        except Exception as e:
            logger.error(f"Error ingesting from URL {url}: {e}")
            return f"❌ Error ingesting from URL: {str(e)}"

    def batch_ingest_directory(
        self, directory_path: str, file_pattern: str = "*", recursive: bool = False
    ) -> str:
        """Ingest multiple files from a directory into both LightRAG and semantic knowledge bases.

        This unified method combines the functionality of the individual batch_ingest_directory
        methods, storing files in both knowledge base systems for comprehensive coverage.

        Args:
            directory_path: Path to the directory containing files
            file_pattern: Glob pattern to match files (e.g., "*.txt", "*.md")
            recursive: Whether to search subdirectories recursively

        Returns:
            Combined summary of ingestion results from both systems.
        """
        try:
            # Expand path shortcuts
            if directory_path.startswith("~/"):
                directory_path = os.path.expanduser(directory_path)
            elif directory_path.startswith("./"):
                directory_path = os.path.abspath(directory_path)

            # Validate directory exists
            if not os.path.exists(directory_path):
                return f"❌ Error: Directory not found at '{directory_path}'"

            if not os.path.isdir(directory_path):
                return f"❌ Error: '{directory_path}' is not a directory"

            # Find files matching pattern
            dir_path = Path(directory_path)
            if recursive:
                files = list(dir_path.rglob(file_pattern))
            else:
                files = list(dir_path.glob(file_pattern))

            # Filter to only include files (not directories)
            files = [f for f in files if f.is_file()]

            if not files:
                return f"❌ No files found matching pattern '{file_pattern}' in '{directory_path}'"

            # Limit batch size to prevent overwhelming the system
            if len(files) > 50:
                return f"❌ Too many files ({len(files)}). Please process in smaller batches (max 50 files)."

            # Track results from both systems
            results = {
                "lightrag": {"success": 0, "failed": 0, "errors": []},
                "semantic": {"success": 0, "failed": 0, "errors": []},
                "total_files": len(files),
                "both_success": 0,
                "partial_success": 0,
                "both_failed": 0,
            }

            # Process files using the unified ingest_file method
            for file_path in files:
                try:
                    result = self.ingest_file(str(file_path))

                    # Parse the unified result to understand what happened
                    if (
                        "✅ Successfully ingested" in result
                        and "both LightRAG and semantic" in result
                    ):
                        # Both succeeded
                        results["both_success"] += 1
                        results["lightrag"]["success"] += 1
                        results["semantic"]["success"] += 1
                        log_debug(
                            f"Successfully ingested into both systems: {file_path.name}"
                        )
                    elif "⚠️ Partial success" in result:
                        # One succeeded, one failed
                        results["partial_success"] += 1
                        if "LightRAG" in result and "succeeded" in result:
                            results["lightrag"]["success"] += 1
                            results["semantic"]["failed"] += 1
                        elif "semantic" in result and "succeeded" in result:
                            results["semantic"]["success"] += 1
                            results["lightrag"]["failed"] += 1
                        logger.warning(
                            f"Partial success for {file_path.name}: {result}"
                        )
                    else:
                        # Both failed
                        results["both_failed"] += 1
                        results["lightrag"]["failed"] += 1
                        results["semantic"]["failed"] += 1
                        results["lightrag"]["errors"].append(
                            f"{file_path.name}: {result}"
                        )
                        results["semantic"]["errors"].append(
                            f"{file_path.name}: {result}"
                        )
                        logger.error(
                            f"Both systems failed for {file_path.name}: {result}"
                        )

                    # Small delay to avoid overwhelming the systems
                    time.sleep(0.5)

                except Exception as e:
                    # Both systems failed due to exception
                    results["both_failed"] += 1
                    results["lightrag"]["failed"] += 1
                    results["semantic"]["failed"] += 1
                    error_msg = f"{file_path.name}: {str(e)}"
                    results["lightrag"]["errors"].append(error_msg)
                    results["semantic"]["errors"].append(error_msg)
                    logger.error(f"Exception processing {file_path.name}: {e}")

            # Format comprehensive results
            summary = f"📊 Unified Batch Ingestion Complete ({results['total_files']} files processed):\n"
            summary += f"✅ Both systems successful: {results['both_success']}\n"
            summary += f"⚠️ Partial success: {results['partial_success']}\n"
            summary += f"❌ Both systems failed: {results['both_failed']}\n\n"

            summary += f"LightRAG Results: {results['lightrag']['success']} successful, {results['lightrag']['failed']} failed\n"
            summary += f"Semantic Results: {results['semantic']['success']} successful, {results['semantic']['failed']} failed"

            # Add error details if any
            if results["lightrag"]["errors"] or results["semantic"]["errors"]:
                summary += "\n\nError Details:"

                # Show unique errors (avoid duplicates from both_failed cases)
                all_errors = set(
                    results["lightrag"]["errors"] + results["semantic"]["errors"]
                )
                error_list = list(all_errors)[:10]  # Limit to 10 errors

                for error in error_list:
                    summary += f"\n- {error}"

                if len(all_errors) > 10:
                    summary += f"\n... and {len(all_errors) - 10} more errors"

            logger.info(
                f"Unified batch ingestion completed: {results['both_success']} fully successful, "
                f"{results['partial_success']} partial, {results['both_failed']} failed out of {results['total_files']} files"
            )
            return summary

        except Exception as e:
            logger.error(f"Error in unified batch ingestion: {e}")
            return f"❌ Error in unified batch ingestion: {str(e)}"

    async def query_knowledge_base(
        self, query: str, mode: Optional[str] = "auto", limit: Optional[int] = 5
    ) -> str:
        """Query the unified knowledge base to retrieve stored factual information and documents.

        This tool is for SEARCHING existing knowledge, NOT for creative tasks like writing stories,
        generating content, or answering general questions. Use this only when you need to find
        specific information that was previously stored in the knowledge base.

        Args:
            query: The search query for finding existing knowledge/documents
            mode: Query mode - "local" (semantic), "global" (graph), "hybrid", "mix", "auto"
            limit: Maximum number of results to return (defaults to 5 if None)

        Returns:
            Search results from the knowledge base, or rejection message for inappropriate requests.
        """
        try:
            if not query or not query.strip():
                return "❌ Error: Query cannot be empty"

            # Filter out inappropriate creative requests
            query_lower = query.lower().strip()

            # Creative/generative request patterns that should NOT use knowledge search
            creative_patterns = [
                "write",
                "create",
                "generate",
                "make",
                "compose",
                "draft",
                "tell me a",
                "give me a",
                "come up with",
                "think of",
                "story",
                "poem",
                "joke",
                "song",
                "essay",
                "article",
                "funny",
                "creative",
                "imagine",
                "pretend",
            ]

            # Check if this looks like a creative request
            if any(pattern in query_lower for pattern in creative_patterns):
                # Additional check: if it's asking for factual info WITH creative words, allow it
                factual_patterns = [
                    "what is",
                    "who is",
                    "when did",
                    "where is",
                    "how does",
                    "definition of",
                    "information about",
                    "facts about",
                    "details about",
                    "explain",
                    "describe",
                ]

                # If it has factual patterns, it might be legitimate
                if not any(factual in query_lower for factual in factual_patterns):
                    logger.info(
                        f"Rejected creative request for knowledge search: {query[:50]}..."
                    )
                    return f"❌ This appears to be a creative request ('{query}'). The knowledge base is for searching existing stored information, not for generating new content. Please rephrase as a search for existing knowledge, or ask me to create content directly without using knowledge tools."

            # Validate mode - handle None case
            valid_modes = ["local", "global", "hybrid", "naive"]
            if mode is None or mode not in valid_modes:
                mode = "auto"

            # Handle None limit
            if limit is None:
                limit = 5

            # Initialize knowledge coordinator if not already done
            if self.knowledge_coordinator is None:
                # Use the agno_knowledge passed to the constructor
                self.knowledge_coordinator = create_knowledge_coordinator(
                    agno_knowledge=self.agno_knowledge,
                    lightrag_url=settings.LIGHTRAG_URL,
                    debug=False,
                )

            # Use the knowledge coordinator for unified querying - now properly async
            result = await self.knowledge_coordinator.query_knowledge_base(
                query=query.strip(),
                mode=mode,
                limit=limit,
                response_type="Multiple Paragraphs",
            )

            logger.info(f"Knowledge query completed: {query[:50]}...")
            return result

        except Exception as e:
            logger.error(f"Error querying knowledge base: {e}")
            return f"❌ Error querying knowledge base: {str(e)}"

    async def query_lightrag_knowledge_direct(
        self,
        query: str,
        params: Optional[Dict] = None,
        url: str = settings.LIGHTRAG_URL,
    ) -> str:
        """Directly query the LightRAG knowledge base and return the raw response.

        This method provides direct, unfiltered access to the LightRAG knowledge base,
        bypassing the intelligent filtering and processing of query_knowledge_base().
        Use this when you need raw access to the knowledge base with custom parameters.

        Args:
            query: The query string to search in the knowledge base
            params: A dictionary of query parameters (mode, response_type, top_k, etc.)
            url: LightRAG server URL (defaults to settings.LIGHTRAG_URL)

        Returns:
            String with query results exactly as LightRAG returns them
        """
        if not query or not query.strip():
            return "❌ Error: Query cannot be empty"

        # Use default parameters if none provided
        if params is None:
            params = {}

        # Set up the query parameters with defaults
        query_params = {
            "query": query.strip(),
            "mode": params.get("mode", "global"),
            "response_type": params.get("response_type", "Multiple Paragraphs"),
            "top_k": params.get("top_k", 10),
            "only_need_context": params.get("only_need_context", False),
            "only_need_prompt": params.get("only_need_prompt", False),
            "stream": params.get("stream", False),
        }

        # Add optional parameters if provided
        if "max_token_for_text_unit" in params:
            query_params["max_token_for_text_unit"] = params["max_token_for_text_unit"]
        if "max_token_for_global_context" in params:
            query_params["max_token_for_global_context"] = params[
                "max_token_for_global_context"
            ]
        if "max_token_for_local_context" in params:
            query_params["max_token_for_local_context"] = params[
                "max_token_for_local_context"
            ]
        if "conversation_history" in params:
            query_params["conversation_history"] = params["conversation_history"]
        if "history_turns" in params:
            query_params["history_turns"] = params["history_turns"]
        if "ids" in params:
            query_params["ids"] = params["ids"]

        try:
            # Use the correct LightRAG URL and endpoint for RAG queries
            final_url = f"{url}/query"

            logger.debug(
                f"Querying KnowledgeBase at {final_url} with params: {query_params}"
            )

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    final_url, json=query_params, timeout=60
                ) as response:
                    if response.status == 200:
                        result = await response.json()

                        # Extract the response content
                        if isinstance(result, dict):
                            content = result.get(
                                "response", result.get("content", str(result))
                            )
                        else:
                            content = str(result)

                        if content and content.strip():
                            logger.info(f"KB direct query successful: {query[:50]}...")
                            return content
                        else:
                            return f"🔍 No relevant knowledge found for '{query}'. Try different keywords or add more knowledge to your base."
                    else:
                        error_text = await response.text()
                        logger.warning(
                            f"KnowledgeBase direct query failed with status {response.status}: {error_text}"
                        )
                        return f"❌ Error querying knowledge base (status {response.status}): {error_text}"

        except aiohttp.ClientError as e:
            logger.error(f"Error connecting to KnowledgeBase server: {e}")
            return f"❌ Error connecting to knowledge base server: {str(e)}"
        except Exception as e:
            logger.error(f"Error querying KnowledgeBase knowledge base: {e}")
            return f"❌ Error querying knowledge base: {str(e)}"

    def ingest_semantic_file(
        self, file_path: str, title: str = None, defer_reload: bool = False
    ) -> str:
        """Ingest a file into the local semantic knowledge base.

        Args:
            file_path: Path to the file to ingest
            title: Optional title for the knowledge entry (defaults to filename)

        Returns:
            Success message or error details.
        """
        try:
            # Expand path shortcuts
            if file_path.startswith("~/"):
                file_path = os.path.expanduser(file_path)
            elif file_path.startswith("./"):
                file_path = os.path.abspath(file_path)

            # Validate file exists
            if not os.path.exists(file_path):
                return f"❌ Error: File not found at '{file_path}'"

            if not os.path.isfile(file_path):
                return f"❌ Error: '{file_path}' is not a file"

            # Get file info
            file_size = os.path.getsize(file_path)
            if file_size > 50 * 1024 * 1024:  # 50MB limit
                return f"❌ Error: File too large ({file_size / (1024*1024):.1f}MB). Maximum size is 50MB."

            filename = os.path.basename(file_path)
            if not title:
                title = os.path.splitext(filename)[0]

            # Check file type
            mime_type, _ = mimetypes.guess_type(file_path)
            supported_types = [
                "text/plain",
                "text/markdown",
                "text/html",
                "text/csv",
                "application/pdf",
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ]

            if mime_type and mime_type not in supported_types:
                logger.warning(f"File type {mime_type} may not be fully supported")

            # Copy file to semantic knowledge directory
            semantic_knowledge_dir = Path(settings.AGNO_KNOWLEDGE_DIR)
            semantic_knowledge_dir.mkdir(parents=True, exist_ok=True)

            # Create unique filename to avoid conflicts
            timestamp = int(time.time())
            file_hash = hashlib.md5(f"{filename}_{timestamp}".encode()).hexdigest()[:8]
            base_name, ext = os.path.splitext(filename)
            unique_filename = f"{base_name}_{file_hash}{ext}"

            dest_path = semantic_knowledge_dir / unique_filename

            # Copy the file
            shutil.copy2(file_path, dest_path)
            log_debug(f"Copied file to semantic knowledge directory: {dest_path}")

            # Reload the knowledge base to include the new file (unless deferred)
            try:
                if self.agno_knowledge:
                    if not defer_reload:
                        logger.debug(
                            "Recreating semantic KB after single file ingestion: %s",
                            filename,
                        )
                        self._reload_knowledge_base_sync(self.agno_knowledge)
                        logger.info(
                            f"Successfully ingested semantic knowledge file: {filename}"
                        )
                        return f"✅ Successfully ingested '{filename}' into semantic knowledge base and reloaded vector embeddings."
                    else:
                        logger.info(
                            f"Successfully ingested semantic knowledge file (reload deferred): {filename}"
                        )
                        return f"✅ Successfully ingested '{filename}' into semantic knowledge base (reload deferred)."
                else:
                    logger.warning("No semantic knowledge base available")
                    return f"⚠️ File copied to semantic directory but no knowledge base available for indexing: '{filename}'"

            except Exception as e:
                # Clean up the copied file if knowledge base reload failed
                try:
                    os.remove(dest_path)
                except OSError:
                    pass
                logger.error(
                    f"Failed to reload knowledge base after adding {filename}: {e}"
                )
                return f"❌ Failed to ingest '{filename}': Error reloading knowledge base - {str(e)}"

        except Exception as e:
            logger.error(f"Error ingesting semantic file {file_path}: {e}")
            return f"❌ Error ingesting file: {str(e)}"

    def ingest_semantic_text(
        self,
        content: str,
        title: str,
        file_type: str = "txt",
        defer_reload: bool = False,
    ) -> str:
        """Ingest text content directly into the local semantic knowledge base.

        Args:
            content: The text content to ingest
            title: Title for the knowledge entry
            file_type: File extension to use (txt, md, html, etc.)

        Returns:
            Success message or error details.
        """
        try:
            if not content or not content.strip():
                return "❌ Error: Content cannot be empty"

            if not title or not title.strip():
                return "❌ Error: Title is required"

            # Validate file_type
            if not file_type.startswith("."):
                file_type = f".{file_type}"

            allowed_types = [".txt", ".md", ".html", ".csv", ".json"]
            if file_type not in allowed_types:
                file_type = ".txt"  # Default to txt

            # Create semantic knowledge directory
            semantic_knowledge_dir = Path(settings.AGNO_KNOWLEDGE_DIR)
            semantic_knowledge_dir.mkdir(parents=True, exist_ok=True)

            # Create unique filename
            timestamp = int(time.time())
            content_hash = hashlib.md5(
                f"{title}_{content[:100]}_{timestamp}".encode()
            ).hexdigest()[:8]
            safe_title = "".join(
                c for c in title if c.isalnum() or c in (" ", "-", "_")
            ).rstrip()
            safe_title = safe_title.replace(" ", "_")[:50]  # Limit length
            filename = f"{safe_title}_{content_hash}{file_type}"

            file_path = semantic_knowledge_dir / filename

            # Write content to file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            log_debug(f"Created semantic knowledge file: {file_path}")

            # Reload the knowledge base to include the new content (unless deferred)
            try:
                if self.agno_knowledge:
                    if not defer_reload:
                        logger.debug(
                            "Recreating semantic KB after single text ingestion: %s",
                            title,
                        )
                        self._reload_knowledge_base_sync(self.agno_knowledge)

                        logger.info(
                            f"Successfully ingested semantic knowledge text: {title}"
                        )
                        return f"✅ Successfully ingested '{title}' into semantic knowledge base and reloaded vector embeddings."
                    else:
                        logger.info(
                            f"Successfully ingested semantic knowledge text (reload deferred): {title}"
                        )
                        return f"✅ Successfully ingested '{title}' into semantic knowledge base (reload deferred)."
                else:
                    logger.warning("No semantic knowledge base available")
                    return f"⚠️ Text saved to semantic directory but no knowledge base available for indexing: '{title}'"

            except Exception as e:
                # Clean up the created file if knowledge base reload failed
                try:
                    os.remove(file_path)
                except OSError:
                    pass
                logger.error(
                    f"Failed to reload knowledge base after adding {title}: {e}"
                )
                return f"❌ Failed to ingest '{title}': Error reloading knowledge base - {str(e)}"

        except Exception as e:
            logger.error(f"Error ingesting semantic text content: {e}")
            return f"❌ Error ingesting text content: {str(e)}"

    def ingest_semantic_from_url(self, url: str, title: str = None) -> str:
        """Ingest content from a URL into the local semantic knowledge base.

        Args:
            url: URL to fetch content from
            title: Optional title for the knowledge entry (defaults to page title or URL)

        Returns:
            Success message or error details.
        """
        try:
            # Validate URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                return f"❌ Error: Invalid URL format: {url}"

            # Fetch content
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }

            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "").lower()

            # Handle different content types
            if "text/html" in content_type:
                # For HTML, try to extract text content
                try:
                    soup = BeautifulSoup(response.content, "html.parser")

                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.decompose()

                    # Get text content
                    content = soup.get_text()

                    # Get title if not provided
                    if not title:
                        title_tag = soup.find("title")
                        title = (
                            title_tag.get_text().strip()
                            if title_tag
                            else parsed_url.netloc
                        )

                    file_type = "html"

                except ImportError:
                    # Fallback if BeautifulSoup not available
                    content = response.text
                    title = title or parsed_url.netloc
                    file_type = "html"

            elif "text/" in content_type or "application/json" in content_type:
                content = response.text
                title = title or parsed_url.netloc
                file_type = "txt" if "text/" in content_type else "json"
            else:
                return f"❌ Error: Unsupported content type: {content_type}"

            # Clean up content
            content = "\n".join(
                line.strip() for line in content.splitlines() if line.strip()
            )

            if not content:
                return f"❌ Error: No content extracted from URL: {url}"

            # Add source URL to content
            content = f"Source: {url}\n\n{content}"

            # Ingest the content
            return self.ingest_semantic_text(content, title, file_type)

        except requests.RequestException as e:
            logger.error(f"Error fetching URL {url}: {e}")
            return f"❌ Error fetching URL: {str(e)}"
        except Exception as e:
            logger.error(f"Error ingesting from URL {url}: {e}")
            return f"❌ Error ingesting from URL: {str(e)}"

    def batch_ingest_semantic_directory(
        self, directory_path: str, file_pattern: str = "*", recursive: bool = False
    ) -> str:
        """Ingest multiple files from a directory into the local semantic knowledge base.

        Args:
            directory_path: Path to the directory containing files
            file_pattern: Glob pattern to match files (e.g., "*.txt", "*.md")
            recursive: Whether to search subdirectories recursively

        Returns:
            Summary of ingestion results.
        """
        try:
            # Expand path shortcuts
            if directory_path.startswith("~/"):
                directory_path = os.path.expanduser(directory_path)
            elif directory_path.startswith("./"):
                directory_path = os.path.abspath(directory_path)

            # Validate directory exists
            if not os.path.exists(directory_path):
                return f"❌ Error: Directory not found at '{directory_path}'"

            if not os.path.isdir(directory_path):
                return f"❌ Error: '{directory_path}' is not a directory"

            # Find files matching pattern
            dir_path = Path(directory_path)
            if recursive:
                files = list(dir_path.rglob(file_pattern))
            else:
                files = list(dir_path.glob(file_pattern))

            # Filter to only include files (not directories)
            files = [f for f in files if f.is_file()]

            if not files:
                return f"❌ No files found matching pattern '{file_pattern}' in '{directory_path}'"

            # Limit batch size to prevent overwhelming the system
            if len(files) > 50:
                return f"❌ Too many files ({len(files)}). Please process in smaller batches (max 50 files)."

            # Process files
            results = {"success": 0, "failed": 0, "errors": []}

            for file_path in files:
                try:
                    result = self.ingest_semantic_file(
                        str(file_path), defer_reload=True
                    )
                    if "✅" in result:
                        results["success"] += 1
                        log_debug(f"Successfully ingested: {file_path.name}")
                    else:
                        results["failed"] += 1
                        results["errors"].append(f"{file_path.name}: {result}")
                        logger.warning(f"Failed to ingest {file_path.name}: {result}")

                    # Small delay to avoid overwhelming the system
                    time.sleep(0.5)

                except Exception as e:
                    results["failed"] += 1
                    error_msg = f"{file_path.name}: {str(e)}"
                    results["errors"].append(error_msg)
                    logger.error(f"Error processing {file_path.name}: {e}")

            # After staging all files, trigger a single recreate if possible
            recreated = False
            try:
                if results["success"] > 0:
                    if self.agno_knowledge:
                        logger.debug(
                            "Recreating semantic knowledge base after staging %d items from '%s'...",
                            results["success"],
                            directory_path,
                        )
                        self._reload_knowledge_base_sync(self.agno_knowledge)
                        logger.info(
                            "Semantic KB recreated successfully after batch ingestion of %d items",
                            results["success"],
                        )
                        recreated = True
                    else:
                        logger.warning(
                            "Semantic KB instance not available to recreate after batch ingestion"
                        )
            except Exception as e:
                logger.error(
                    "Failed to recreate semantic KB after batch ingestion: %s", e
                )

            # Format results
            summary = f"📊 Batch semantic ingestion complete: {results['success']} successful, {results['failed']} failed"

            if recreated:
                summary += (
                    "\n\n✅ Semantic knowledge base recreated after batch ingestion."
                )
            elif results["success"] > 0 and not self.agno_knowledge:
                summary += "\n\n⚠️ Files ingested but no semantic knowledge base available to recreate."

            if results["errors"]:
                summary += f"\n\nErrors:\n" + "\n".join(
                    f"- {error}" for error in results["errors"][:10]
                )
                if len(results["errors"]) > 10:
                    summary += f"\n... and {len(results['errors']) - 10} more errors"

            logger.info(
                f"Batch semantic ingestion completed: {results['success']}/{len(files)} files successful"
            )
            return summary

        except Exception as e:
            logger.error(f"Error in batch semantic ingestion: {e}")
            return f"❌ Error in batch semantic ingestion: {str(e)}"

    def query_semantic_knowledge(self, query: str, limit: int = 10) -> str:
        """Query the local semantic knowledge base to retrieve stored information.

        This tool searches the local LanceDB-based semantic knowledge base using vector
        similarity search. It's designed for finding factual information and documents
        that were previously ingested into the semantic knowledge base.

        Args:
            query: The search query for finding existing knowledge/documents
            limit: Maximum number of results to return

        Returns:
            Search results from the semantic knowledge base.
        """
        try:
            if not query or not query.strip():
                return "❌ Error: Query cannot be empty"

            # Filter out inappropriate creative requests
            query_lower = query.lower().strip()

            # Creative/generative request patterns that should NOT use knowledge search
            creative_patterns = [
                "write",
                "create",
                "generate",
                "make",
                "compose",
                "draft",
                "tell me a",
                "give me a",
                "come up with",
                "think of",
                "story",
                "poem",
                "joke",
                "song",
                "essay",
                "article",
                "funny",
                "creative",
                "imagine",
                "pretend",
            ]

            # Check if this looks like a creative request
            if any(pattern in query_lower for pattern in creative_patterns):
                # Additional check: if it's asking for factual info WITH creative words, allow it
                factual_patterns = [
                    "what is",
                    "who is",
                    "when did",
                    "where is",
                    "how does",
                    "definition of",
                    "information about",
                    "facts about",
                    "details about",
                    "explain",
                    "describe",
                ]

                # If it has factual patterns, it might be legitimate
                if not any(factual in query_lower for factual in factual_patterns):
                    logger.info(
                        f"Rejected creative request for semantic knowledge search: {query[:50]}..."
                    )
                    return f"❌ This appears to be a creative request ('{query}'). The semantic knowledge base is for searching existing stored information, not for generating new content. Please rephrase as a search for existing knowledge, or ask me to create content directly without using knowledge tools."

            # Get the knowledge base
            try:
                if not self.agno_knowledge:
                    return "❌ No semantic knowledge base available. Please ensure the knowledge base is properly initialized."

                # Perform semantic search
                search_results = self.agno_knowledge.search(
                    query.strip(), num_documents=limit
                )

                if not search_results:
                    logger.info(f"No semantic search results found for: {query}")
                    return f"🔍 No relevant knowledge found for '{query}'. Try different keywords or add more knowledge to your semantic knowledge base."

                # Format results
                result = f"🧠 SEMANTIC KNOWLEDGE SEARCH (found {len(search_results)} results):\n\n"

                for i, doc in enumerate(search_results, 1):
                    # Extract content from the document
                    content = str(doc)
                    # Truncate long content for display
                    if len(content) > 200:
                        content = content[:200] + "..."

                    result += f"{i}. {content}\n\n"

                logger.info(f"Semantic knowledge search successful: {query[:50]}...")
                return result

            except Exception as e:
                logger.error(f"Error querying semantic knowledge base: {e}")
                return f"❌ Error querying semantic knowledge base: {str(e)}"

        except Exception as e:
            logger.error(f"Error in semantic knowledge query: {e}")
            return f"❌ Error in semantic knowledge query: {str(e)}"

    def recreate_semantic_kb(self) -> str:
        """Recreate the semantic knowledge base by reloading all knowledge files.

        This method rebuilds the vector embeddings and search indices for the semantic
        knowledge base, which is useful after batch ingestion or when the knowledge
        base becomes out of sync.

        Returns:
            Success message or error details.
        """
        try:
            if not self.agno_knowledge:
                return "❌ No semantic knowledge base available for recreation."

            # Recreate the knowledge base
            self._reload_knowledge_base_sync(self.agno_knowledge)

            logger.info("Successfully recreated semantic knowledge base")
            return "✅ Semantic knowledge base has been successfully recreated with updated vector embeddings."

        except Exception as e:
            logger.error(f"Error recreating semantic knowledge base: {e}")
            return f"❌ Error recreating semantic knowledge base: {str(e)}"

    # Unified ingestion methods that combine both LightRAG and semantic operations
    def ingest_file(self, file_path: str, title: str = None) -> str:
        """Ingest a file into both LightRAG and semantic knowledge bases.

        This unified method combines the functionality of ingest_knowledge_file and
        ingest_semantic_file, storing the content in both knowledge base systems
        for comprehensive coverage.

        Args:
            file_path: Path to the file to ingest
            title: Optional title for the knowledge entry (defaults to filename)

        Returns:
            Combined success/error message from both operations.
        """
        try:
            # Validate inputs first
            if not file_path or not file_path.strip():
                return "❌ Error: File path cannot be empty"

            # Expand path shortcuts
            if file_path.startswith("~/"):
                file_path = os.path.expanduser(file_path)
            elif file_path.startswith("./"):
                file_path = os.path.abspath(file_path)

            # Validate file exists
            if not os.path.exists(file_path):
                return f"❌ Error: File not found at '{file_path}'"

            if not os.path.isfile(file_path):
                return f"❌ Error: '{file_path}' is not a file"

            filename = os.path.basename(file_path)
            if not title:
                title = os.path.splitext(filename)[0]

            # Track results from both operations
            results = {"lightrag": None, "semantic": None}

            # Attempt LightRAG ingestion
            try:
                lightrag_result = self.ingest_knowledge_file(file_path, title)
                results["lightrag"] = lightrag_result
                logger.debug(
                    f"LightRAG ingestion result for {filename}: {lightrag_result[:100]}..."
                )
            except Exception as e:
                results["lightrag"] = f"❌ LightRAG error: {str(e)}"
                logger.error(f"LightRAG ingestion failed for {filename}: {e}")

            # Attempt semantic ingestion
            try:
                semantic_result = self.ingest_semantic_file(file_path, title)
                results["semantic"] = semantic_result
                logger.debug(
                    f"Semantic ingestion result for {filename}: {semantic_result[:100]}..."
                )
            except Exception as e:
                results["semantic"] = f"❌ Semantic error: {str(e)}"
                logger.error(f"Semantic ingestion failed for {filename}: {e}")

            # Determine overall success
            lightrag_success = results["lightrag"] is not None and "✅" in str(
                results["lightrag"]
            )
            semantic_success = results["semantic"] is not None and "✅" in str(
                results["semantic"]
            )

            if lightrag_success and semantic_success:
                logger.info(
                    f"Successfully ingested '{filename}' into both knowledge bases"
                )
                return f"✅ Successfully ingested '{filename}' into both LightRAG and semantic knowledge bases."
            elif lightrag_success or semantic_success:
                # Partial success
                success_systems = []
                failed_systems = []

                if lightrag_success:
                    success_systems.append("LightRAG")
                else:
                    failed_systems.append(f"LightRAG ({results['lightrag']})")

                if semantic_success:
                    success_systems.append("semantic")
                else:
                    failed_systems.append(f"semantic ({results['semantic']})")

                logger.warning(
                    f"Partial success ingesting '{filename}': {success_systems} succeeded, {failed_systems} failed"
                )
                return f"⚠️ Partial success for '{filename}': {', '.join(success_systems)} succeeded. Failed: {', '.join(failed_systems)}"
            else:
                # Both failed
                logger.error(f"Both ingestion methods failed for '{filename}'")
                return f"❌ Failed to ingest '{filename}' into both knowledge bases:\n- LightRAG: {results['lightrag']}\n- Semantic: {results['semantic']}"

        except Exception as e:
            logger.error(f"Error in unified file ingestion for {file_path}: {e}")
            return f"❌ Error in unified file ingestion: {str(e)}"

    def ingest_text(self, content: str, title: str, file_type: str = "txt") -> str:
        """Ingest text content into both LightRAG and semantic knowledge bases.

        This unified method combines the functionality of ingest_knowledge_text and
        ingest_semantic_text, storing the content in both knowledge base systems
        for comprehensive coverage.

        Args:
            content: The text content to ingest
            title: Title for the knowledge entry
            file_type: File extension to use (txt, md, html, etc.)

        Returns:
            Combined success/error message from both operations.
        """
        try:
            # Validate inputs
            if not content or not content.strip():
                return "❌ Error: Content cannot be empty"

            if not title or not title.strip():
                return "❌ Error: Title is required"

            # Track results from both operations
            results = {"lightrag": None, "semantic": None}

            # Attempt LightRAG ingestion
            try:
                lightrag_result = self.ingest_knowledge_text(content, title, file_type)
                results["lightrag"] = lightrag_result
                logger.debug(
                    f"LightRAG text ingestion result for '{title}': {lightrag_result[:100]}..."
                )
            except Exception as e:
                results["lightrag"] = f"❌ LightRAG error: {str(e)}"
                logger.error(f"LightRAG text ingestion failed for '{title}': {e}")

            # Attempt semantic ingestion
            try:
                semantic_result = self.ingest_semantic_text(content, title, file_type)
                results["semantic"] = semantic_result
                logger.debug(
                    f"Semantic text ingestion result for '{title}': {semantic_result[:100]}..."
                )
            except Exception as e:
                results["semantic"] = f"❌ Semantic error: {str(e)}"
                logger.error(f"Semantic text ingestion failed for '{title}': {e}")

            # Determine overall success
            lightrag_success = results["lightrag"] is not None and "✅" in str(
                results["lightrag"]
            )
            semantic_success = results["semantic"] is not None and "✅" in str(
                results["semantic"]
            )

            if lightrag_success and semantic_success:
                logger.info(
                    f"Successfully ingested text '{title}' into both knowledge bases"
                )
                return f"✅ Successfully ingested '{title}' into both LightRAG and semantic knowledge bases."
            elif lightrag_success or semantic_success:
                # Partial success
                success_systems = []
                failed_systems = []

                if lightrag_success:
                    success_systems.append("LightRAG")
                else:
                    failed_systems.append(f"LightRAG ({results['lightrag']})")

                if semantic_success:
                    success_systems.append("semantic")
                else:
                    failed_systems.append(f"semantic ({results['semantic']})")

                logger.warning(
                    f"Partial success ingesting text '{title}': {success_systems} succeeded, {failed_systems} failed"
                )
                return f"⚠️ Partial success for '{title}': {', '.join(success_systems)} succeeded. Failed: {', '.join(failed_systems)}"
            else:
                # Both failed
                logger.error(f"Both text ingestion methods failed for '{title}'")
                return f"❌ Failed to ingest '{title}' into both knowledge bases:\n- LightRAG: {results['lightrag']}\n- Semantic: {results['semantic']}"

        except Exception as e:
            logger.error(f"Error in unified text ingestion for '{title}': {e}")
            return f"❌ Error in unified text ingestion: {str(e)}"

    def ingest_url(self, url: str, title: str = None) -> str:
        """Ingest content from a URL into both LightRAG and semantic knowledge bases.

        This unified method combines the functionality of ingest_knowledge_from_url and
        ingest_semantic_from_url, storing the content in both knowledge base systems
        for comprehensive coverage.

        Args:
            url: URL to fetch content from
            title: Optional title for the knowledge entry (defaults to page title or URL)

        Returns:
            Combined success/error message from both operations.
        """
        try:
            # Validate URL
            if not url or not url.strip():
                return "❌ Error: URL cannot be empty"

            from urllib.parse import urlparse

            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                return f"❌ Error: Invalid URL format: {url}"

            # Track results from both operations
            results = {"lightrag": None, "semantic": None}

            # Attempt LightRAG ingestion
            try:
                lightrag_result = self.ingest_knowledge_from_url(url, title)
                results["lightrag"] = lightrag_result
                logger.debug(
                    f"LightRAG URL ingestion result for '{url}': {lightrag_result[:100]}..."
                )
            except Exception as e:
                results["lightrag"] = f"❌ LightRAG error: {str(e)}"
                logger.error(f"LightRAG URL ingestion failed for '{url}': {e}")

            # Attempt semantic ingestion
            try:
                semantic_result = self.ingest_semantic_from_url(url, title)
                results["semantic"] = semantic_result
                logger.debug(
                    f"Semantic URL ingestion result for '{url}': {semantic_result[:100]}..."
                )
            except Exception as e:
                results["semantic"] = f"❌ Semantic error: {str(e)}"
                logger.error(f"Semantic URL ingestion failed for '{url}': {e}")

            # Determine overall success
            lightrag_success = results["lightrag"] is not None and "✅" in str(
                results["lightrag"]
            )
            semantic_success = results["semantic"] is not None and "✅" in str(
                results["semantic"]
            )

            display_title = title or url
            if lightrag_success and semantic_success:
                logger.info(
                    f"Successfully ingested URL '{url}' into both knowledge bases"
                )
                return f"✅ Successfully ingested '{display_title}' from URL into both LightRAG and semantic knowledge bases."
            elif lightrag_success or semantic_success:
                # Partial success
                success_systems = []
                failed_systems = []

                if lightrag_success:
                    success_systems.append("LightRAG")
                else:
                    failed_systems.append(f"LightRAG ({results['lightrag']})")

                if semantic_success:
                    success_systems.append("semantic")
                else:
                    failed_systems.append(f"semantic ({results['semantic']})")

                logger.warning(
                    f"Partial success ingesting URL '{url}': {success_systems} succeeded, {failed_systems} failed"
                )
                return f"⚠️ Partial success for '{display_title}': {', '.join(success_systems)} succeeded. Failed: {', '.join(failed_systems)}"
            else:
                # Both failed
                logger.error(f"Both URL ingestion methods failed for '{url}'")
                return f"❌ Failed to ingest '{display_title}' from URL into both knowledge bases:\n- LightRAG: {results['lightrag']}\n- Semantic: {results['semantic']}"

        except Exception as e:
            logger.error(f"Error in unified URL ingestion for '{url}': {e}")
            return f"❌ Error in unified URL ingestion: {str(e)}"

    def _reload_knowledge_base_sync(self, knowledge_base):
        """Reload the knowledge base synchronously to avoid event loop issues."""
        try:
            # Use the synchronous load method instead of async
            knowledge_base.load(recreate=True)
            logger.info("Successfully reloaded semantic knowledge base")
        except Exception as e:
            logger.error(f"Error reloading knowledge base: {e}")
            raise

    def _upload_to_lightrag(
        self, file_path: Path, filename: str, url: str = settings.LIGHTRAG_URL
    ) -> str:
        """Upload a file to the LightRAG server.

        Args:
            file_path: Path to the file to upload
            filename: Name to use for the uploaded file
            url: LightRAG server URL to upload to

        Returns:
            Success message or error details.
        """
        try:
            final_url = f"{url}/documents/upload"

            with open(file_path, "rb") as f:
                files = {"file": (filename, f, "application/octet-stream")}
                response = requests.post(final_url, files=files, timeout=60)

                if response.status_code in [200, 201]:
                    result = response.json()
                    logger.info(f"Successfully uploaded to KnowledgeBase: {filename}")
                    return "✅ File uploaded and processing started"
                else:
                    error_text = response.text
                    logger.error(f"KnowledgeBase upload failed: {error_text}")
                    return f"Upload failed: {error_text}"

        except requests.RequestException as e:
            logger.error(f"Error uploading to KnowledgeBase: {e}")
            return f"Upload error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error during upload: {e}")
            return f"Unexpected upload error: {str(e)}"
