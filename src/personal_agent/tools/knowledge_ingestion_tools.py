"""
Knowledge Ingestion Tools for Personal Agent.

This module provides tools for easily ingesting files and content into the LightRAG
knowledge base, making it simple for users to add new knowledge through natural conversation.
"""

import asyncio
import hashlib
import mimetypes
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import List, Optional, Union
from urllib.parse import urlparse

import aiohttp
import requests
from agno.tools import Toolkit
from agno.utils.log import log_debug

from ..config import settings
from ..utils import setup_logging

logger = setup_logging(__name__)


class KnowledgeIngestionTools(Toolkit):
    """
    Knowledge ingestion tools for adding files and content to the knowledge base.

    Args:
        ingest_file (bool): Enable file ingestion functionality.
        ingest_text (bool): Enable direct text ingestion functionality.
        ingest_url (bool): Enable URL content ingestion functionality.
        batch_ingest (bool): Enable batch directory ingestion functionality.
        query_knowledge (bool): Enable unified knowledge querying functionality.
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
            tools.append(self.ingest_knowledge_file)
        if ingest_text:
            tools.append(self.ingest_knowledge_text)
        if ingest_url:
            tools.append(self.ingest_knowledge_from_url)
        if batch_ingest:
            tools.append(self.batch_ingest_directory)
        if query_knowledge:
            tools.append(self.query_knowledge_base)

        super().__init__(name="knowledge_ingestion", tools=tools, **kwargs)

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
            upload_result = self._upload_to_lightrag(dest_path, unique_filename)

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
            upload_result = self._upload_to_lightrag(file_path, filename)

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
                    from bs4 import BeautifulSoup

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
        """Ingest multiple files from a directory into the knowledge base.

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
                    result = self.ingest_knowledge_file(str(file_path))
                    if "✅" in result:
                        results["success"] += 1
                        log_debug(f"Successfully ingested: {file_path.name}")
                    else:
                        results["failed"] += 1
                        results["errors"].append(f"{file_path.name}: {result}")
                        logger.warning(f"Failed to ingest {file_path.name}: {result}")

                    # Small delay to avoid overwhelming the server
                    time.sleep(0.5)

                except Exception as e:
                    results["failed"] += 1
                    error_msg = f"{file_path.name}: {str(e)}"
                    results["errors"].append(error_msg)
                    logger.error(f"Error processing {file_path.name}: {e}")

            # Format results
            summary = f"📊 Batch ingestion complete: {results['success']} successful, {results['failed']} failed"

            if results["errors"]:
                summary += f"\n\nErrors:\n" + "\n".join(
                    f"- {error}" for error in results["errors"][:10]
                )
                if len(results["errors"]) > 10:
                    summary += f"\n... and {len(results['errors']) - 10} more errors"

            logger.info(
                f"Batch ingestion completed: {results['success']}/{len(files)} files successful"
            )
            return summary

        except Exception as e:
            logger.error(f"Error in batch ingestion: {e}")
            return f"❌ Error in batch ingestion: {str(e)}"

    def query_knowledge_base(self, query: str, mode: str = "auto", limit: int = 5) -> str:
        """Query the unified knowledge base to retrieve stored factual information and documents.
        
        This tool is for SEARCHING existing knowledge, NOT for creative tasks like writing stories,
        generating content, or answering general questions. Use this only when you need to find
        specific information that was previously stored in the knowledge base.

        Args:
            query: The search query for finding existing knowledge/documents
            mode: Query mode - "local" (semantic), "global" (graph), "hybrid", "mix", "auto"
            limit: Maximum number of results to return

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
                "write", "create", "generate", "make", "compose", "draft",
                "tell me a", "give me a", "come up with", "think of",
                "story", "poem", "joke", "song", "essay", "article",
                "funny", "creative", "imagine", "pretend"
            ]
            
            # Check if this looks like a creative request
            if any(pattern in query_lower for pattern in creative_patterns):
                # Additional check: if it's asking for factual info WITH creative words, allow it
                factual_patterns = [
                    "what is", "who is", "when did", "where is", "how does",
                    "definition of", "information about", "facts about",
                    "details about", "explain", "describe"
                ]
                
                # If it has factual patterns, it might be legitimate
                if not any(factual in query_lower for factual in factual_patterns):
                    logger.info(f"Rejected creative request for knowledge search: {query[:50]}...")
                    return f"❌ This appears to be a creative request ('{query}'). The knowledge base is for searching existing stored information, not for generating new content. Please rephrase as a search for existing knowledge, or ask me to create content directly without using knowledge tools."

            # Validate mode
            valid_modes = ["local", "global", "hybrid", "mix", "naive", "auto"]
            if mode not in valid_modes:
                mode = "auto"

            # Auto mode: intelligent routing based on query characteristics
            if mode == "auto":
                query_lower = query.lower()
                
                # Use global mode for relationship queries
                relationship_keywords = ["relationship", "connection", "related", "link", "between", "how", "why"]
                if any(keyword in query_lower for keyword in relationship_keywords):
                    mode = "global"
                # Use local mode for specific fact queries
                elif any(keyword in query_lower for keyword in ["what", "when", "where", "who", "define"]):
                    mode = "local"
                # Use hybrid for complex queries
                else:
                    mode = "hybrid"

            # Query LightRAG server
            try:
                url = f"{settings.LIGHTRAG_URL}/query"
                params = {
                    "query": query.strip(),
                    "mode": mode,
                    "top_k": limit,
                    "response_type": "Multiple Paragraphs"
                }

                response = requests.post(url, json=params, timeout=60)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Extract the response content
                    if isinstance(result, dict):
                        content = result.get('response', result.get('content', str(result)))
                    else:
                        content = str(result)
                    
                    if content and content.strip():
                        logger.info(f"Knowledge query successful: {query[:50]}...")
                        return f"🧠 KNOWLEDGE BASE QUERY (mode: {mode}):\n\n{content}"
                    else:
                        return f"🔍 No relevant knowledge found for '{query}'. Try different keywords or add more knowledge to your base."
                        
                else:
                    error_text = response.text
                    logger.warning(f"LightRAG query failed: {error_text}")
                    return f"❌ Error querying knowledge base: {error_text}"
                    
            except requests.RequestException as e:
                logger.error(f"Error connecting to LightRAG server: {e}")
                return f"❌ Error connecting to knowledge base server: {str(e)}"

        except Exception as e:
            logger.error(f"Error querying knowledge base: {e}")
            return f"❌ Error querying knowledge base: {str(e)}"

    def _upload_to_lightrag(self, file_path: Path, filename: str) -> str:
        """Upload a file to the LightRAG server.

        Args:
            file_path: Path to the file to upload
            filename: Name to use for the uploaded file

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
                    logger.info(
                        f"Successfully uploaded to LightRAG server {final_url}: {filename}"
                    )
                    return f"✅ File uploaded and processing started"
                else:
                    error_text = response.text
                    logger.error(f"LightRAG upload failed: {error_text}")
                    return f"Upload failed: {error_text}"

        except requests.RequestException as e:
            logger.error(f"Error uploading to LightRAG: {e}")
            return f"Upload error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error during upload: {e}")
            return f"Unexpected upload error: {str(e)}"
