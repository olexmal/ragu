# Browser Use MCP Configuration Guide

This guide explains how to configure Browser Use MCP (Model Context Protocol) server for Cursor.

## What is Browser Use MCP?

Browser Use MCP is a Model Context Protocol server that enables AI assistants to automate web browser tasks, such as:
- Navigating to websites
- Taking screenshots
- Filling forms
- Clicking buttons
- Extracting content from web pages

## Prerequisites

1. **Python 3.11+** installed
2. **uv package manager** installed (for running MCP servers)
3. **Chrome or Chromium** browser installed

## Installation

### Step 1: Install Browser Use

```bash
uv pip install 'browser-use'
```

Or using pip directly:
```bash
pip install browser-use
```

### Step 2: Verify Installation

```bash
uvx browser-use --help
```

## Configuration for Cursor

### Option A: Workspace-Level Configuration (Recommended)

Create or edit `.cursor/mcp.json` in your project root:

```json
{
  "mcpServers": {
    "browser-use": {
      "command": "uvx",
      "args": ["browser-use", "--mcp"],
      "env": {
        "OPENAI_API_KEY": "your-openai-api-key-here"
      }
    }
  }
}
```

### Option B: User-Level Configuration

Edit `~/.config/cursor/mcp.json` (or `%APPDATA%\Cursor\mcp.json` on Windows):

```json
{
  "mcpServers": {
    "browser-use": {
      "command": "uvx",
      "args": ["browser-use", "--mcp"],
      "env": {
        "OPENAI_API_KEY": "your-openai-api-key-here"
      }
    }
  }
}
```

## Environment Variables

You can configure Browser Use behavior using environment variables:

```json
{
  "mcpServers": {
    "browser-use": {
      "command": "uvx",
      "args": ["browser-use", "--mcp"],
      "env": {
        "OPENAI_API_KEY": "your-openai-api-key-here",
        "ANTHROPIC_API_KEY": "your-anthropic-api-key-here",
        "BROWSER_USE_HEADLESS": "false",
        "BROWSER_USE_DISABLE_SECURITY": "false"
      }
    }
  }
}
```

### Available Environment Variables

- **`OPENAI_API_KEY`** (required): Your OpenAI API key for browser automation
- **`ANTHROPIC_API_KEY`** (optional): Alternative to OpenAI API key
- **`BROWSER_USE_HEADLESS`** (optional): Set to `"false"` to see the browser window (default: `"true"`)
- **`BROWSER_USE_DISABLE_SECURITY`** (optional): Set to `"true"` to disable browser security features (not recommended)

## Verification

After configuration:

1. **Restart Cursor** to load the MCP configuration
2. **Test the connection** by asking Cursor to:
   - "Navigate to example.com and take a screenshot"
   - "Search for 'browser automation' on Google"

## Troubleshooting

### Issue: MCP server not connecting

**Solution:**
- Verify `uvx` is in your PATH: `which uvx`
- Check that Browser Use is installed: `uvx browser-use --help`
- Ensure Chrome/Chromium is installed
- Check Cursor's MCP logs (usually in Cursor's output panel)

### Issue: Browser window not visible

**Solution:**
- Set `BROWSER_USE_HEADLESS` to `"false"` in the environment variables
- Ensure no other browser instances are using the same profile

### Issue: API key errors

**Solution:**
- Verify your OpenAI API key is correct
- Ensure the API key has necessary permissions
- Check that the key is properly set in the `env` section of the config

### Issue: Browser automation fails

**Solution:**
- Ensure Chrome/Chromium is installed and accessible
- Try setting `BROWSER_USE_DISABLE_SECURITY` to `"true"` (use with caution)
- Check browser console for errors

## Example Usage

Once configured, you can use Browser Use MCP in Cursor:

```
User: "Navigate to https://angular.io/docs and take a screenshot of the main page"
```

Cursor will use the Browser Use MCP server to:
1. Launch a browser
2. Navigate to the URL
3. Take a screenshot
4. Return the result

## Security Considerations

⚠️ **Important Security Notes:**

- Browser Use MCP can execute arbitrary browser actions
- Only use with trusted AI assistants
- Be cautious with `BROWSER_USE_DISABLE_SECURITY`
- Keep your API keys secure and never commit them to version control
- Consider using environment variables or secure credential storage

## Alternative: Cursor Browser Extension MCP

Cursor also has a built-in browser extension MCP server (`cursor-browser-extension`) that may already be configured. Check if it's available in your Cursor settings before adding Browser Use MCP.

## Additional Resources

- [Browser Use Documentation](https://docs.browser-use.com/)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Cursor MCP Documentation](https://cursor.sh/docs)

