# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is an MCP (Model Context Protocol) server implementation for AnswerRocket's analytics platform. The server automatically creates separate MCP servers for each copilot (AI assistant) in an AnswerRocket instance, enabling focused interactions with individual copilots through LLM clients.

## Key Commands

### Development
```bash
# Run the server locally with environment variables
AR_URL="https://your-instance.answerrocket.com" AR_TOKEN="your-token" COPILOT_ID="copilot-id" uv run python server.py

# Test MCP server functionality
uv run mcp inspect server.py

# Get copilot metadata
uv run python get_copilots.py "AR_URL" "AR_TOKEN"
```

### Installation & Setup
```bash
# Install dependencies using uv
uv venv server/venv --python 3.10.7
uv add "mcp[cli]"
uv add "git+ssh://git@github.com/answerrocket/answerrocket-python-client.git@get-copilots-for-mcp"

# Install MCP server for a specific copilot
uv run mcp install server.py -n "copilot-name" -v AR_URL="url" -v AR_TOKEN="token" -v COPILOT_ID="id" --with "git+ssh://git@github.com/answerrocket/answerrocket-python-client.git@get-copilots-for-mcp"
```

## Architecture

### Multi-Copilot Server Architecture
- Each copilot in AnswerRocket gets its own dedicated MCP server instance
- Server names follow pattern: `{copilot-name}-Assistant`
- Each server requires three environment variables: `AR_URL`, `AR_TOKEN`, `COPILOT_ID`
- Servers are stateless and can be started/stopped independently

### Core Components

1. **server.py**: Main MCP server implementation
   - Uses FastMCP framework for high-performance async operations
   - Dynamically discovers and registers copilot skills as MCP tools
   - Implements parallel skill fetching and registration
   - Provides proper ToolAnnotations for each skill

2. **get_copilots.py**: Utility for copilot discovery
   - Connects to AnswerRocket instance
   - Fetches all available copilots and their metadata
   - Outputs JSON for consumption by install script

3. **install.sh**: Automated installer
   - Detects OS and installs uv package manager
   - Sets up Python 3.10.7 environment
   - Discovers copilots and creates individual MCP servers
   - Handles all dependency installation

### Dynamic Skill Registration

The server dynamically creates MCP tools from AnswerRocket skills:
- Extracts parameters from GraphQL schema fields
- Creates proper function signatures with type annotations
- Handles required/optional parameters
- Validates constrained values
- Provides detailed error messages

### Key Design Patterns

1. **Async-First**: Uses asyncio for parallel operations when fetching and registering skills
2. **Dynamic Function Generation**: Creates tool functions at runtime based on skill metadata
3. **Proper Error Handling**: Validates connections, parameters, and provides detailed error messages
4. **Type Safety**: Uses Python type hints and MCP ToolAnnotations

## Important Implementation Details

- The AnswerRocket Python client is installed from a specific git branch: `get-copilots-for-mcp`
- Python 3.10.7 is specifically required (enforced by uv)
- Each skill's parameters are mapped from AnswerRocket's GraphQL schema
- The `isMulti` field determines if a parameter accepts arrays
- The `constrainedValues` field provides allowed values for validation
- Skills without default values are marked as required parameters

## Common Tasks

When modifying the server:
1. Always test with `uv run mcp inspect server.py` after changes
2. Ensure environment variables are set before running
3. Check skill parameter extraction logic in `extract_skill_parameters()` function
4. Verify async operations in `initialize_skill_tools_async()`

When adding new features:
1. Follow the existing async patterns for performance
2. Add proper ToolAnnotations for any new tools
3. Ensure error messages are descriptive and actionable
4. Test with multiple copilots to ensure compatibility