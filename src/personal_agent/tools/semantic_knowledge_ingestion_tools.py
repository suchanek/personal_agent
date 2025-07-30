"""
Semantic Knowledge Ingestion Tools for Personal Agent.

This module provides tools for easily ingesting files and content into the local
LanceDB-based semantic knowledge base, making it simple for users to add new knowledge
through natural conversation for local semantic search capabilities.

This complements the LightRAG knowledge ingestion tools by providing equivalent
functionality for the local semantic knowledge base using LanceDB vector storage.
"""

import hashlib
import mimetypes
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import List, Optional, Union
from urllib.parse import urlparse

import requests
from agno.tools import Toolkit
from agno.utils.log import log_debug
from bs4 import BeautifulSoup

from ..config import settings
from ..core.agno_storage import create_combined_knowledge_base, load_combined_knowledge_base
from ..utils import setup_logging

logger = setup_logging(__name__)


class SemanticKnowledgeIngestionTools(Toolkit):
    """
    Semantic knowledge ingestion tools for adding files and content to the local LanceDB knowledge base.

    Args:
        ingest_file (bool): Enable file ingestion functionality.
        ingest_text (bool): Enable direct text ingestion functionality.
        ingest_url (bool): Enable URL content ingestion functionality.
        batch_ingest (bool): Enable batch directory ingestion functionality.
        query_knowledge (bool): Enable semantic knowledge querying functionality.
    """

    def __init__(
        self,
        ingest_file: bool = True,
        ingest_text: bool = True,
        ingest_url: bool = True,
        batch_ingest: bool = True,
        query_knowledge: bool = True,
        **kwargs,
    ):
        tools = []

        if ingest_file:
            tools.append(self.ingest_semantic_file)
        if ingest_text:
            tools.append(self.ingest_semantic_text)
        if ingest_url:
            tools.append(self.ingest_semantic_from_url)
        if batch_ingest:
            tools.append(self.batch_ingest_semantic_directory)
        if query_knowledge:
            tools.append(self.query_semantic_knowledge)

        super().__init__(name="semantic_knowledge_ingestion", tools=tools, **kwargs)

        # Initialize knowledge base reference
        self._knowledge_base = None

    def _get_knowledge_base(self):
        """Get or create the semantic knowledge base instance."""
        if self._knowledge_base is None:
            self._knowledge_base = create_combined_knowledge_base()
            if self._knowledge_base is None:
                raise RuntimeError("Failed to create semantic knowledge base")
        return self._knowledge_base

    def _reload_knowledge_base_sync(self, knowledge_base):
        """Reload the knowledge base synchronously to avoid event loop issues."""
        try:
            # Use the synchronous load method instead of async
            knowledge_base.load(recreate=True)
            logger.info("Successfully reloaded semantic knowledge base")
        except Exception as e:
            logger.error(f"Error reloading knowledge base: {e}")
            raise

    def ingest_semantic_file(self, file_path: str, title: str = None) -> str:
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
            semantic_knowledge_dir = Path(settings.DATA_DIR) / "knowledge"
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

            # Reload the knowledge base to include the new file
            try:
                knowledge_base = self._get_knowledge_base()
                # Recreate the knowledge base to include new files
                self._reload_knowledge_base_sync(knowledge_base)
                
                logger.info(f"Successfully ingested semantic knowledge file: {filename}")
                return f"✅ Successfully ingested '{filename}' into semantic knowledge base and reloaded vector embeddings."
                
            except Exception as e:
                # Clean up the copied file if knowledge base reload failed
                try:
                    os.remove(dest_path)
                except OSError:
                    pass
                logger.error(f"Failed to reload knowledge base after adding {filename}: {e}")
                return f"❌ Failed to ingest '{filename}': Error reloading knowledge base - {str(e)}"

        except Exception as e:
            logger.error(f"Error ingesting semantic file {file_path}: {e}")
            return f"❌ Error ingesting file: {str(e)}"

    def ingest_semantic_text(
        self, content: str, title: str, file_type: str = "txt"
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
            semantic_knowledge_dir = Path(settings.DATA_DIR) / "knowledge"
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

            # Reload the knowledge base to include the new content
            try:
                knowledge_base = self._get_knowledge_base()
                # Recreate the knowledge base to include new files
                self._reload_knowledge_base_sync(knowledge_base)
                
                logger.info(f"Successfully ingested semantic knowledge text: {title}")
                return f"✅ Successfully ingested '{title}' into semantic knowledge base and reloaded vector embeddings."
                
            except Exception as e:
                # Clean up the created file if knowledge base reload failed
                try:
                    os.remove(file_path)
                except OSError:
                    pass
                logger.error(f"Failed to reload knowledge base after adding {title}: {e}")
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
                    result = self.ingest_semantic_file(str(file_path))
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

            # Format results
            summary = f"📊 Batch semantic ingestion complete: {results['success']} successful, {results['failed']} failed"

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

    def query_semantic_knowledge(
        self, query: str, limit: int = 10
    ) -> str:
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
                knowledge_base = self._get_knowledge_base()
                
                # Perform semantic search
                search_results = knowledge_base.search(query.strip(), num_documents=limit)
                
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
