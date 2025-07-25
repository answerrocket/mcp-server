# Max MCP Server

A Model Context Protocol (MCP) server that connects Claude and other AI assistants to AnswerRocket's Max AI platform, enabling access to Max copilots and their skills directly from your AI conversations.

## Quick Start for Claude Desktop Users (.dxt install)

### Prerequisites

**macOS:**
- Install `uv` via Homebrew: `brew install uv`
- If you already have `uv` installed via another method, uninstall and reinstall with Homebrew:
  ```bash
  # Remove existing uv data and binaries
  uv cache clean
  rm -r "$(uv python dir)"
  rm -r "$(uv tool dir)"
  rm ~/.local/bin/uv ~/.local/bin/uvx
  
  # Install via Homebrew
  brew install uv
  ```

**Windows/Linux:**
- Follow the installation instructions at [uv Installation Guide](https://docs.astral.sh/uv/getting-started/installation/)

### Installation

1. **Download the .dxt file:** [mcp-server.dxt](https://github.com/answerrocket/mcp-server/releases)

2. **Install Claude Desktop** if you haven't already

3. **Double-click the .dxt file** to open it with Claude Desktop

4. **Click "Install"** when prompted

5. **Configure your Max instance:**
   - **Max URL:** Enter your Max instance URL (e.g., `http://localhost:8080` or `https://maxai.dev.answerrocket.com`)
     - Include the `http://` or `https://` prefix
     - Do not include any path components
   - **SDK Key:** Get this from your Max instance frontend
   - **Agent ID:** This is the copilot ID from Skill Studio
     - Navigate to Skill Studio: `https://your-max-instance/apps/system/skill-studio/`
     - The URL pattern is: `/skill-studio/{COPILOT_ID}/skills/{SKILL_ID}`
     - Copy the first UUID (COPILOT_ID)

6. **Click "Save"** (keep the setup window open)

7. **Enable the MCP server** using the toggle in the upper left

### Verification

Navigate back to Claude Desktop's home screen and click the tools icon. You should see "Max MCP" with a list of tools identical to those available in your Max Agent/Copilot.

**Note:** This feature requires Max instances on version 25.09 or above.

## Web-based Usage (Coming Soon)

Support for web-based AI assistants like claude.ai and chatgpt.com is in the works.

## Development Setup

### Prerequisites

- Python 3.10+
- Git
- Access to a Max instance

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/answerrocket/mcp-server.git
   cd mcp-server
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

### Environment Variables

The server supports two modes: **local** and **remote**.

#### Local Mode (Direct API Access)

For development and testing with direct API access to Max:

```bash
export MCP_MODE=local
export AR_URL=http://superstoredev.local.answerrocket.com:1234 # or where your instance is located. It does not have to be a local Max instance.
export AR_TOKEN=arc-your-token-here
export COPILOT_ID=your-copilot-uuid
export MCP_TRANSPORT=stdio
```

#### Remote Mode (OAuth)

For production deployments with OAuth authentication:

```bash
export MCP_MODE=remote
export MCP_TRANSPORT=streamable-http
export MCP_HOST=localhost
export MCP_PORT=9090
```

**Note:** In remote mode, the `AR_URL` is automatically derived from incoming requests, enabling true multi-tenancy.

### URL Patterns

When running in remote mode, the server accepts requests at:

```
http://your-server:port/mcp/agent/{COPILOT_ID}
```

For example:
- `http://superstoredev.local.answerrocket.com:1234/mcp/agent/0d91262d-e039-43c3-8022-0d285af703d4`

This URL pattern is typically routed through your AnswerRocket instance's nginx configuration.

### Testing with MCP Inspector

We highly recommend using the [MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector) for development and testing:

```bash
npx @modelcontextprotocol/inspector
```

Version 0.16.1 is buggy and does not play well. If that is the case, you should use version 0.16.0
```bash
npx @modelcontextprotocol/inspector@0.16.0
```

## Local Development with Claude Desktop

You can test your local development server directly with Claude Desktop by configuring your `claude_desktop_config.json`:

### Configuration File Location

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

### Example Configuration

```json
{
  "mcpServers": {
    "max-mcp-dev": {
      "command": "/path/to/mcp-server/.venv/bin/python",
      "args": [
        "/path/to/mcp-server/mcp_server/__main__.py"
      ],
      "env": {
        "AR_URL": "http://your-max-instance:port",
        "AR_TOKEN": "your-sdk-token",
        "COPILOT_ID": "your-copilot-uuid"
      }
    }
  }
}
```

**Important:** Replace the example values with your actual:
- Max instance URL
- SDK token
- Copilot ID

After saving the configuration, restart Claude Desktop to apply the changes.

## Remote Deployment with OAuth

For production deployments with OAuth authentication:

### Max Instance Configuration

Your Max instance must have OAuth server enabled:

```bash
export ENABLE_OAUTH_SERVER=true
./overmind.sh --overlay=superstoredev,ricedemo
```

### Multi-Tenant Testing

To test multiple tenants, configure your Max instance with multiple tenant overlays and ensure your OAuth server supports the tenant domains you want to test.

### Server Deployment

1. **Set environment variables:**
   ```bash
   export MCP_MODE=remote
   export MCP_TRANSPORT=streamable-http
   export MCP_HOST=0.0.0.0  # or your server IP
   export MCP_PORT=9090
   ```

2. **Run the server:**
   ```bash
   maxai-mcp
   ```
   or 
   ```bash
   uv run python mcp_server/__main__.py
   ```

### OAuth Flow

In remote mode, the server:
1. Validates OAuth tokens against the requesting domain's introspection endpoint
2. Dynamically determines the Max instance URL from the request context
3. Registers tools/skills specific to the requested copilot ID
4. Supports multiple Max instances simultaneously without configuration changes

## API Reference

### Supported Transports

- **stdio:** For direct integration with Desktop apps
- **streamable-http:** For web-based integrations and production deployments

### Authentication

- **Local mode:** Uses SDK tokens for direct API access
- **Remote mode:** Uses OAuth 2.0 with Bearer tokens

### Dynamic Tool Registration

The server dynamically loads and registers tools based on:
- The copilot ID in the request URL
- Available skills in the specified Max copilot
- User permissions and authentication context
