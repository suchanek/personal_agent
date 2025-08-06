"""Firecrawl reader for web scraping (optional dependency)."""

import os

try:
    from agno.document.reader.firecrawl_reader import FirecrawlReader
    FIRECRAWL_AVAILABLE = True
except ImportError:
    FIRECRAWL_AVAILABLE = False
    FirecrawlReader = None

def create_firecrawl_reader():
    """Create a FirecrawlReader instance if available."""
    if not FIRECRAWL_AVAILABLE:
        raise ImportError("FirecrawlReader requires the 'firecrawl-py' package. Install it with: pip install firecrawl-py")
    
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        raise ValueError("FIRECRAWL_API_KEY environment variable is required")
    
    return FirecrawlReader(
        api_key=api_key,
        mode="scrape",
        chunk=True,
        params={"formats": ["markdown"]},
    )

def scrape_url(url: str):
    """Scrape a URL using Firecrawl if available."""
    if not FIRECRAWL_AVAILABLE:
        print("Firecrawl is not available. Install with: pip install firecrawl-py")
        return None
    
    try:
        reader = create_firecrawl_reader()
        print(f"Starting scrape of {url}...")
        documents = reader.read(url)

        if documents:
            for doc in documents:
                print(doc.name)
                print(doc.content)
                print(f"Content length: {len(doc.content)}")
                print("-" * 80)
            return documents
        else:
            print("No documents were returned")
            return None

    except Exception as e:
        print(f"Error type: {type(e)}")
        print(f"Error occurred: {str(e)}")
        return None

# Example usage (only runs if this file is executed directly)
if __name__ == "__main__":
    scrape_url("https://github.com/agno-agi/agno")
