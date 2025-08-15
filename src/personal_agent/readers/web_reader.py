"""Web reader for scraping websites using Agno WebsiteReader."""

from agno.document.reader.website_reader import WebsiteReader


def create_web_reader(max_depth=3, max_links=10):
    """Create a WebsiteReader instance with specified parameters."""
    return WebsiteReader(max_depth=max_depth, max_links=max_links)


def read_website(url: str, max_depth=3, max_links=10):
    """Read content from a website URL."""
    reader = create_web_reader(max_depth=max_depth, max_links=max_links)

    try:
        print(f"Starting read of {url}...")
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
    read_website("https://docs.agno.com/introduction")
