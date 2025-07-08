# AnswerRocket Multi-Copilot MCP Server

An MCP (Model Context Protocol) server that provides access to AnswerRocket's analytics and insights platform. This server automatically creates **separate MCP servers for each copilot** in your AnswerRocket instance, allowing dedicated, focused interactions with individual copilots through LLM clients.

## Features

- 🚀 **Multi-Copilot Architecture**: Automatically creates separate MCP servers for each copilot in your AnswerRocket instance
- 🎯 **Dedicated Copilot Servers**: Each copilot gets its own MCP server with copilot-specific tools and capabilities  
- 🛠️ **Skill Operations**: List, inspect, and run specific skills within each copilot
- 💬 **Interactive Q&A**: Ask questions directly to specific AnswerRocket copilots and receive insights

## Quick Install

Install the AnswerRocket MCP Server with a single command:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/answerrocket/mcp-server/refs/heads/main/bootstrap.sh)"
```

The installer will:
1. Check system requirements (git, curl)
2. Install uv package manager (if not already installed)
3. Install and configure Python 3.10.7 using uv
4. Prompt you for your AnswerRocket URL
5. Guide you to generate an API key from your AnswerRocket instance
6. Set up a Python virtual environment with uv
7. Install all dependencies (including AnswerRocket SDK from git repository)
8. Discover all copilots in your AnswerRocket instance
9. Create and install separate MCP servers for each copilot

### Bootstrap vs Install Scripts

This project uses a two-stage installation process:

**`bootstrap.sh`** - The entry point script that:
- Can be downloaded and run with a single `curl` command
- Clones the full repository to a permanent, cross-platform application directory
- Ensures all required files (`lib/`, `scripts/`, etc.) are available
- Runs the main installer and passes through any command-line arguments
- Handles updates by fetching the latest changes from the repository

**`install.sh`** - The main installer script that:
- Performs the actual installation steps listed above
- Always works with the local repository (no remote cloning)
- Depends on modular library files in `lib/` and utility scripts in `scripts/`
- Handles system setup, dependency installation, and MCP server configuration
- Used for development work when you have a local clone

**Installation Locations:**
- **macOS**: `~/Library/Application Support/AnswerRocket/mcp-server`
- **Linux**: `~/.local/share/answerrocket/mcp-server`
- **Windows**: `%APPDATA%/AnswerRocket/mcp-server`

The bootstrap approach allows us to maintain clean, modular code while providing a convenient single-command installation experience and proper application directory structure.

## Manual Installation

If you prefer to install manually:

### Prerequisites

- Git
- curl (for downloading uv)
- An AnswerRocket instance with API access

**Note**: Python 3.10.7 will be automatically installed by the installer using uv.

### Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/answerrocket/mcp-server-demo.git
   cd mcp-server-demo
   ```

2. **Install uv package manager:**
   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Windows
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

3. **Create and activate a virtual environment with uv:**
   ```bash
   uv venv --python 3.10.7
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

4. **Install dependencies:**
   ```bash
   uv add "mcp[cli]"
   uv add "git+ssh://git@github.com/answerrocket/answerrocket-python-client.git@get-copilots-for-mcp"
   ```

5. **Get your API credentials:**
   - Go to `{YOUR_AR_URL}/apps/chat/topics?panel=user-info`
   - Click "Generate" under "Client API Key"
   - Copy the generated API key

6. **Create copilot metadata script:**
   ```bash
   uv run python get_copilots.py "{YOUR_AR_URL}" "{YOUR_API_TOKEN}"
   ```

7. **Install MCP servers for each copilot:**
   ```bash
   # This will create a separate server for each copilot
   uv run mcp install server.py -n "answerrocket-copilot-{COPILOT_ID}" -v AR_URL="{YOUR_AR_URL}" -v AR_TOKEN="{YOUR_API_TOKEN}" -v COPILOT_ID="{COPILOT_ID}" --with "git+ssh://git@github.com/answerrocket/answerrocket-python-client.git@get-copilots-for-mcp"
   ```

## Available Tools (Per Copilot Server)

Each copilot gets its own dedicated MCP server with the following tools:

### `ask_question`
Ask a question to this specific AnswerRocket copilot and receive insights with visualizations.

**Parameters:**
- `fully_contextualized_question` (string): Your question with full context

### `get_copilot_info`
Get detailed information about this copilot, including its available skills.

**Parameters:**
- `use_published_version` (boolean, optional): Use published version (default: true)

### `get_skill_info`
Get detailed information about a specific skill within this copilot.

**Parameters:**
- `skill_id` (string): The ID of the skill
- `use_published_version` (boolean, optional): Use published version (default: true)

### `run_skill`
Execute a specific skill within this copilot with optional parameters.

**Parameters:**
- `skill_name` (string): The name of the skill to run
- `parameters` (object, optional): Parameters to pass to the skill

## How It Works

The installer automatically:
1. Discovers all copilots in your AnswerRocket instance
2. Creates a separate MCP server for each copilot  
3. Each server is named `answerrocket-copilot-{copilot-id}`
4. Each server's tools are specific to that copilot (no need to specify copilot ID)

**Benefits:**
- ✅ Clean namespace separation per copilot
- ✅ No need to specify copilot IDs in tool calls
- ✅ Easy to manage individual copilot servers
- ✅ Better organization for teams with multiple copilots

## Usage Examples

### Basic Question Asking
```javascript
// Using the copilot-specific MCP server (no copilot_id needed!)
await callTool('ask_question', {
  fully_contextualized_question: 'What were our top performing products last quarter?'
});
```

### Exploring Copilots
```javascript
// Get information about this copilot
const copilotInfo = await callTool('get_copilot_info');

// List available skills
console.log('Available skills:', copilotInfo.skill_ids);
```

### Running Skills
```javascript
// Run a specific skill on this copilot
await callTool('run_skill', {
  skill_name: 'Revenue Analysis',
  parameters: {
    time_period: 'last_quarter',
    breakdown: 'by_product'
  }
});
```

## Configuration

Each copilot server requires three environment variables:

- `AR_URL`: Your AnswerRocket instance URL (e.g., `https://your-instance.answerrocket.com`)
- `AR_TOKEN`: Your AnswerRocket API token
- `COPILOT_ID`: The specific copilot ID for this server

These are automatically configured during installation. The installer:
1. Discovers all copilots using the `get_copilots.py` script
2. Creates a separate server for each copilot with its unique `COPILOT_ID`
3. Names each server `answerrocket-copilot-{copilot-id}`

## Troubleshooting

### Common Issues

1. **"ERROR: No matching distribution found for mcp[cli]"**
   - This is usually due to an old pip version
   - The installer now automatically upgrades pip first
   - If you still see this error, manually run: `python -m pip install --upgrade pip`

2. **"Cannot connect to AnswerRocket"**
   - Verify your `AR_URL` is correct and accessible
   - Check that your `AR_TOKEN` is valid and not expired

3. **"Python version not supported"**
   - The installer should automatically install Python 3.10.7 using uv
   - If you see this error, try running: `uv python install 3.10.7`
   - Check your Python version with: `uv run python --version`

4. **"mcp command not found"**
   - Try running: `uv add "mcp[cli]"`
   - Ensure your virtual environment is created with uv: `uv venv --python 3.10.7`
   - Check if the installation was successful: `uv run mcp --help`

5. **"No copilots found"**
   - Check that your API token has the correct permissions
   - Verify you can access copilots through the AnswerRocket web interface

### Getting Help

- Check the [AnswerRocket documentation](https://docs.answerrocket.com/)
- Visit the [MCP specification](https://modelcontextprotocol.io/) for protocol details
- Open an issue on this repository for bug reports

## Development

To contribute or modify the server:

1. **Clone and install in development mode:**
   ```bash
   git clone https://github.com/answerrocket/mcp-server-demo.git
   cd mcp-server-demo
   ```

2. **Run the installer for development (uses local repository):**
   ```bash
   ./install.sh
   ```

3. **Run the server locally:**
   ```bash
   uv run python src/answerrocket_mcp/server.py
   ```

4. **Test with the MCP inspector:**
   ```bash
   uv run mcp inspect src/answerrocket_mcp/server.py
   ```

**Note**: When developing, always use `./install.sh` directly. The `bootstrap.sh` script is only for end-users who want to install from the remote repository.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support with AnswerRocket integration, please contact [AnswerRocket support](https://answerrocket.com/support).

For MCP protocol questions, refer to the [Model Context Protocol documentation](https://modelcontextprotocol.io/).
