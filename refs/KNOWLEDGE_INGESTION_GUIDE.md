# Knowledge Ingestion System Guide

This guide explains how to use the new knowledge ingestion system in the Personal Agent to easily add files and content to your knowledge base.

## Overview

The knowledge ingestion system provides a seamless way to add new knowledge to your personal agent through natural conversation. It supports multiple input methods and automatically processes content through the LightRAG server for intelligent querying.

## Features

### 🔄 Multi-Modal Ingestion
- **File Ingestion**: Upload files directly from your filesystem
- **Text Ingestion**: Add content directly through conversation
- **URL Ingestion**: Extract and ingest content from web pages
- **Batch Processing**: Process multiple files from directories

### 📁 Format Support
- Text files (`.txt`, `.md`, `.html`, `.csv`, `.json`)
- PDF documents (`.pdf`)
- Microsoft Word documents (`.docx`, `.doc`)
- Web content (HTML pages)

### 🧠 Intelligent Processing
- Automatic file type detection
- Content deduplication
- Metadata preservation
- Progress tracking and error handling
- Integration with LightRAG knowledge graph

## Usage Examples

### Through Natural Conversation

Once the agent is running, you can use these natural language commands:

```
"Please ingest the file ~/Documents/research_paper.pdf into my knowledge base"

"Add this text to my knowledge base: [your content here]"

"Ingest content from https://example.com/article"

"Process all markdown files from ~/Projects/notes/"

"Add the contents of ~/Downloads/report.docx to my knowledge"
```

### Available Tools

The system provides these tools that the agent can use:

#### `ingest_knowledge_file`
Ingest a file into the knowledge base.
- **Parameters**: `file_path` (required), `title` (optional)
- **Example**: `ingest_knowledge_file("~/Documents/notes.md", "Meeting Notes")`

#### `ingest_knowledge_text`
Ingest text content directly.
- **Parameters**: `content` (required), `title` (required), `file_type` (optional)
- **Example**: `ingest_knowledge_text("Important information...", "Key Facts", "md")`

#### `ingest_knowledge_from_url`
Ingest content from a URL.
- **Parameters**: `url` (required), `title` (optional)
- **Example**: `ingest_knowledge_from_url("https://example.com/article", "Research Article")`

#### `batch_ingest_directory`
Process multiple files from a directory.
- **Parameters**: `directory_path` (required), `file_pattern` (optional), `recursive` (optional)
- **Example**: `batch_ingest_directory("~/Documents/", "*.pdf", True)`

#### `query_knowledge_base`
Query the unified knowledge base.
- **Parameters**: `query` (required), `mode` (optional), `limit` (optional)
- **Example**: `query_knowledge_base("machine learning concepts", "hybrid", 5)`

## System Architecture

### Components

1. **KnowledgeIngestionTools**: Agno toolkit providing ingestion capabilities
2. **KnowledgeManager**: Orchestrates knowledge operations and server communication
3. **LightRAG Integration**: Processes content for intelligent querying
4. **File Management**: Handles local file storage and organization

### Workflow

1. **File Staging**: Files are copied to the knowledge directory
2. **LightRAG Upload**: Content is uploaded via `/documents/upload` endpoint
3. **Processing**: LightRAG extracts entities and relationships
4. **Indexing**: Content becomes searchable through various query modes
5. **Verification**: System confirms successful ingestion

### Storage Paths

- **Knowledge Directory**: `{DATA_DIR}/{STORAGE_BACKEND}/{USER_ID}/knowledge`
- **LightRAG Storage**: Managed by LightRAG server
- **Metadata**: Tracked in local database

## Configuration

### Environment Variables

The system uses these configuration settings:

```bash
# LightRAG Server Configuration
LIGHTRAG_URL=http://localhost:9621
LIGHTRAG_MEMORY_URL=http://localhost:9622

# Storage Configuration
AGNO_KNOWLEDGE_DIR=/Users/Shared/personal_agent_data/agno/{USER_ID}/knowledge
AGNO_STORAGE_DIR=/Users/Shared/personal_agent_data/agno/{USER_ID}

# User Configuration
USER_ID=your_user_id
```

### Server Requirements

- **LightRAG Server**: Must be running and accessible
- **Docker**: Required for LightRAG server (if using Docker deployment)
- **Network Access**: Required for URL ingestion

## Query Modes

The system supports different query modes for retrieving knowledge:

### `local`
- Focuses on context-dependent information
- Best for specific facts and details
- Uses entity-based retrieval

### `global`
- Utilizes global knowledge relationships
- Best for understanding connections
- Uses relationship-based retrieval

### `hybrid`
- Combines local and global approaches
- Balanced retrieval strategy
- Good for complex queries

### `mix`
- Integrates knowledge graph and vector retrieval
- Comprehensive search approach
- Best for exploratory queries

### `auto` (default)
- Intelligent routing based on query characteristics
- Automatically selects optimal mode
- Recommended for general use

## Error Handling

The system provides comprehensive error handling:

### Common Issues

1. **File Not Found**: Verify file path exists and is accessible
2. **Server Offline**: Ensure LightRAG server is running
3. **File Too Large**: Maximum file size is 50MB
4. **Unsupported Format**: Check supported file types
5. **Network Error**: Required for URL ingestion

### Error Messages

- ✅ Success: Green checkmark with confirmation
- ❌ Error: Red X with specific error details
- ⚠️ Warning: Yellow warning for partial success
- 🔄 Processing: Blue circle for ongoing operations

## Monitoring and Management

### Knowledge Statistics

Get information about your knowledge base:

```python
from personal_agent.core.knowledge_manager import KnowledgeManager

manager = KnowledgeManager(user_id="your_id")
stats = await manager.get_knowledge_stats()
```

### Sync Validation

Ensure local and server knowledge are synchronized:

```python
sync_status = await manager.validate_knowledge_sync()
```

### Pipeline Status

Monitor processing pipeline:

```python
pipeline_status = await manager.get_pipeline_status()
```

## Best Practices

### File Organization

1. **Use Descriptive Titles**: Provide meaningful titles for better searchability
2. **Organize by Topic**: Group related files in directories
3. **Regular Cleanup**: Remove outdated or duplicate content
4. **Batch Processing**: Use batch ingestion for multiple files

### Content Quality

1. **Clean Text**: Ensure content is well-formatted
2. **Relevant Information**: Focus on valuable knowledge
3. **Proper Metadata**: Include relevant topics and categories
4. **Regular Updates**: Keep knowledge base current

### Performance Optimization

1. **File Size**: Keep files under 50MB for optimal processing
2. **Batch Size**: Process max 50 files at once
3. **Server Resources**: Monitor LightRAG server performance
4. **Network Bandwidth**: Consider bandwidth for URL ingestion

## Troubleshooting

### Server Connection Issues

```bash
# Check server status
curl http://localhost:9621/health

# Restart LightRAG server
./restart-lightrag.sh
```

### Storage Issues

```bash
# Check disk space
df -h

# Verify permissions
ls -la /Users/Shared/personal_agent_data/
```

### Processing Issues

```bash
# Check pipeline status
curl http://localhost:9621/documents/pipeline_status

# Clear cache if needed
curl -X POST http://localhost:9621/documents/clear_cache
```

## Testing

Run the test script to verify system functionality:

```bash
python test_knowledge_ingestion.py
```

This will test:
- Server connectivity
- Text ingestion
- File ingestion
- URL ingestion (if network available)
- Knowledge querying
- Statistics and sync validation

## Integration Examples

### CLI Usage

```bash
# Start the agent
poetry run paga_cli

# Then use natural language:
> "Please ingest ~/Documents/research.pdf"
> "Add all markdown files from ~/Notes/ to my knowledge base"
```

### Streamlit Interface

```bash
# Start the web interface
poetry run paga_streamlit

# Use the chat interface or file upload widget
```

### Programmatic Usage

```python
from personal_agent.tools.knowledge_ingestion_tools import KnowledgeIngestionTools

tools = KnowledgeIngestionTools()

# Ingest a file
result = tools.ingest_knowledge_file("~/Documents/notes.txt")

# Ingest text content
result = tools.ingest_knowledge_text(
    content="Important information...",
    title="Key Facts"
)

# Query knowledge
result = tools.query_knowledge_base("machine learning")
```

## Future Enhancements

### Planned Features

1. **Drag & Drop Interface**: Web-based file upload
2. **Real-time Processing**: Live progress updates
3. **Content Summarization**: Automatic content summaries
4. **Version Control**: Track knowledge changes over time
5. **Export Capabilities**: Export knowledge in various formats

### API Extensions

1. **Bulk Operations**: Enhanced batch processing
2. **Metadata Management**: Rich metadata support
3. **Content Validation**: Automatic quality checks
4. **Integration Hooks**: Webhook support for external systems

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Review system logs for error details
3. Verify server status and configuration
4. Test with the provided test script

The knowledge ingestion system makes it easy to build and maintain a comprehensive personal knowledge base through natural conversation with your AI agent.
