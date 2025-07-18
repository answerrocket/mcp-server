"""MCP Server entry point for the AnswerRocket MCP server."""

import sys
import os
from typing import cast, Literal
from mcp_server.server import create_server
from mcp_server.utils import EnvironmentValidator

# Global MCP server instance
mcp = None

def validate_environment_for_mode(mode: str) -> bool:
    """Validate environment variables based on mode."""
    if mode == "local":
        # Local mode requires AR_URL, AR_TOKEN, and COPILOT_ID
        ar_url = os.getenv("AR_URL")
        ar_token = os.getenv("AR_TOKEN")
        copilot_id = os.getenv("COPILOT_ID")
        
        print(f"Mode: {mode}", file=sys.stderr)
        print(f"AR_URL: {'✓' if ar_url else '✗'}", file=sys.stderr)
        print(f"AR_TOKEN: {'✓' if ar_token else '✗'}", file=sys.stderr)
        print(f"COPILOT_ID: {'✓' if copilot_id else '✗'}", file=sys.stderr)
        
        if not all([ar_url, ar_token, copilot_id]):
            print("Error: Missing required environment variables for local mode", file=sys.stderr)
            print("Please set AR_URL, AR_TOKEN, and COPILOT_ID", file=sys.stderr)
            return False
            
    elif mode == "remote":
        # Remote mode only requires AR_URL (other URLs are derived)
        ar_url = os.getenv("AR_URL")
        mcp_host = os.getenv("MCP_HOST", "localhost")
        mcp_port = os.getenv("MCP_PORT", "9090")
        
        print(f"Mode: {mode}", file=sys.stderr)
        print(f"AR_URL: {'✓' if ar_url else '✗'}", file=sys.stderr)
        print(f"MCP_HOST: {mcp_host}", file=sys.stderr)
        print(f"MCP_PORT: {mcp_port}", file=sys.stderr)
        print(f"AUTH_SERVER_URL: {ar_url} (derived from AR_URL)", file=sys.stderr)
        
        # Determine protocol and construct resource server URL for display
        protocol = "http" if mcp_host in ["127.0.0.1", "localhost"] else "https"
        resource_server_url = f"{protocol}://{mcp_host}:{mcp_port}"
        print(f"RESOURCE_SERVER_URL: {resource_server_url} (derived from MCP_HOST:MCP_PORT)", file=sys.stderr)
        
        if not ar_url:
            print("Error: Missing required environment variable for remote mode", file=sys.stderr)
            print("Please set AR_URL", file=sys.stderr)
            return False
    else:
        print(f"Error: Unknown mode '{mode}'. Use 'local' or 'remote'", file=sys.stderr)
        return False
    
    return True

def initialize_server():
    """Initialize the global MCP server."""
    global mcp
    
    # Get mode from environment
    mode = EnvironmentValidator.get_mcp_mode()
    
    # Validate environment for the selected mode
    if not validate_environment_for_mode(mode):
        sys.exit(1)
    
    print(f"Creating MCP server in {mode} mode...", file=sys.stderr)
    try:
        mcp = create_server()
        print("✓ MCP server created successfully!", file=sys.stderr)
    except Exception as e:
        print(f"Error creating MCP server: {e}", file=sys.stderr)
        sys.exit(1)
    
    return mcp

def main():
    """Main entry point when running as a script."""
    server = initialize_server()
    transport = cast(Literal["stdio", "sse", "streamable-http"], os.getenv("MCP_TRANSPORT", "stdio"))
    if server:
        print(f"Running MCP server in {transport} mode...", file=sys.stderr)
        server.run(transport=transport)

if __name__ == "__main__":
    main()