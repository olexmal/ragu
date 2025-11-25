# Changelog

All notable changes to the RAG System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0] - 2025-01-27

### Added

#### Web Interface
- **Modern Angular Web UI** - Beautiful, responsive web interface for all operations
- **Query Interface** - Interactive query page with version selection and query options
- **Query History** - View, search, and rerun previous queries
- **Dashboard** - System overview with quick actions and statistics
- **Upload & Import Page** - Unified interface for document upload and Confluence import
  - Document upload with drag-and-drop support
  - Confluence page import via page ID or URL
  - Version and overwrite options
- **Collections Management** - View and manage document collections with version information
- **Monitoring Dashboard** - System statistics, query analytics, and performance metrics
- **Settings Management** - Configure system, Confluence, and LLM/embedding provider settings
- **Authentication UI** - Login page with session management
- **Help Icons** - Contextual help tooltips throughout the interface
- **Error Handling** - User-friendly error messages and loading states

#### Confluence Integration
- **Confluence Import Endpoint** - `POST /confluence/import` for importing Confluence pages
- **Markdown Conversion** - Automatic conversion of Confluence pages to Markdown using `confluence-markdown-exporter`
- **Page ID/URL Support** - Import pages using page ID or full Confluence URL
- **Version Tagging** - Support for version-specific Confluence imports
- **Settings Management** - Configure Confluence connection settings via web UI

#### Backend Enhancements
- **Confluence Import Function** - `import_confluence_page_to_vector_db()` for processing Confluence pages
- **Multiple LLM Provider Support** - Support for Ollama, OpenAI, Anthropic, Azure OpenAI, Google, and OpenRouter
- **Embedding Provider Abstraction** - Configurable embedding providers
- **Settings API** - Endpoints for managing system, Confluence, and provider settings
- **Session Management** - Secure session handling for web UI authentication

#### Dependencies
- Added `confluence-markdown-exporter==1.0.4` for Confluence page conversion

### Changed
- **Settings Page** - Removed "Page Configuration" and "Sync Settings" sections (moved to Upload & Import page)
- **Navigation** - Updated menu structure with "Upload & Import" replacing "Upload Documents"
- **Routing** - Updated routes to reflect new page structure

### Fixed
- File descriptor leak in temporary file handling for Confluence imports
- Operator precedence issues in authentication credential extraction
- Type validation for `page_id` and `overwrite` parameters
- Subprocess handling for CLI tool execution
- Error handling consistency across command format variants

---

## [1.0.0] - 2025-01-27

### Added

#### Core Features
- Document embedding with support for PDF, HTML, TXT, and Markdown
- Incremental updates (append to existing collections without overwriting)
- Version-aware collections for documentation versioning
- Natural language querying with RAG
- Multi-query retrieval for better context
- Source document citation in responses

#### API Endpoints
- `POST /embed` - Embed single file
- `POST /embed-batch` - Embed multiple files
- `POST /query` - Query documentation
- `GET /health` - Health check
- `GET /collections` - List all collections
- `GET /collections/<version>` - Get collection info
- `DELETE /collections/<version>` - Delete collection
- `POST /query/multi-version` - Query across multiple versions
- `POST /query/compare` - Compare answers across versions
- `GET /history` - Query history
- `GET /history/search` - Search history
- `GET /history/export` - Export history
- `GET /favorites` - Get favorites
- `POST /favorites` - Add favorite
- `DELETE /favorites` - Remove favorite
- `GET /stats` - System statistics
- `POST /cache/clear` - Clear cache
- `POST /extract-code` - Extract code examples
- `GET /auth/status` - Authentication status

#### Advanced Features
- Multi-version querying across documentation versions
- Query history and favorites management
- Query result caching with TTL
- Code example extraction from documentation
- Export functionality (JSON/CSV)
- Monitoring and analytics

#### Security
- Path traversal protection
- Input validation
- Optional API key authentication
- Write-only protection mode
- Secure key generation

#### Automation
- Pre-commit hooks configuration
- Scheduled update scripts
- Webhook handler for version updates
- Cron job setup utility
- Automatic version change detection

#### Integration
- Maven integration for Javadoc embedding
- Copilot instructions for GitHub Copilot
- Developer guide documentation
- CLI tools for all operations

#### Testing
- Unit tests for all modules
- Integration tests
- Test configuration and fixtures
- Test runner script

### Configuration

- Environment variable support via `.env`
- Configurable models, paths, and settings
- Optional authentication configuration
- Monitoring and caching configuration

### Documentation

- Comprehensive README
- Developer guide
- API documentation
- Copilot integration guide
- Implementation plan

---

## Future Enhancements

### Planned (Optional)
- IDE plugin (VS Code extension)
- Slack/Discord bot integration
- Relationship graph generation
- Model quantization support
- Advanced analytics and visualization
- Multi-language support

---

[1.1.0]: https://github.com/your-org/ragu/releases/tag/v1.1.0
[1.0.0]: https://github.com/your-org/ragu/releases/tag/v1.0.0
