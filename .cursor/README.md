# Cursor IDE Configuration

This folder contains configuration files for Cursor IDE to provide better context and coding assistance for the RAG System project.

## Files

### `rules`
Coding standards, style guidelines, and best practices for the project. Includes:
- Technology stack overview
- Code style guidelines for Python and TypeScript
- Architecture patterns
- Design system (DESIGNO) guidelines
- Common patterns and conventions
- Security practices

### `context`
Project context and architecture information. Includes:
- Project description and features
- Project structure
- API endpoints documentation
- Data flow diagrams
- State management patterns
- Environment variables
- Development workflow
- Common tasks and how-tos

### `ignore`
Files and directories that should be excluded from Cursor's context to improve performance and relevance. Includes:
- Build outputs
- Dependencies (node_modules, venv)
- Data directories (chroma, logs)
- IDE files
- Temporary files

## Usage

Cursor IDE automatically reads these files to:
- Provide better code suggestions
- Understand project architecture
- Follow coding standards
- Avoid suggesting changes to ignored files
- Maintain consistency across the codebase

## Updating

When adding new features or changing architecture:
1. Update `context` with new information
2. Update `rules` if coding standards change
3. Update `ignore` if new directories should be excluded

