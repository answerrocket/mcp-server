"""MCP Server entry point for the AnswerRocket MCP server."""

import sys
import os
from typing import cast, Literal
from .server import create_server

# Global MCP server instance
mcp = None

def initialize_server():
    """Initialize the global MCP server."""
    global mcp
    
    print("Testing AnswerRocket MCP server setup...", file=sys.stderr)
    
    # Check environment variables
    ar_url = os.getenv("AR_URL")
    ar_token = os.getenv("AR_TOKEN")
    copilot_id = os.getenv("COPILOT_ID")
    
    print(f"AR_URL: {'✓' if ar_url else '✗'}", file=sys.stderr)
    print(f"AR_TOKEN: {'✓' if ar_token else '✗'}", file=sys.stderr)
    print(f"COPILOT_ID: {'✓' if copilot_id else '✗'}", file=sys.stderr)
    
    if not all([ar_url, ar_token, copilot_id]):
        print("Error: Missing required environment variables", file=sys.stderr)
        print("Please set AR_URL, AR_TOKEN, and COPILOT_ID", file=sys.stderr)
        sys.exit(1)
    
    print("Creating MCP server...", file=sys.stderr)
    mcp = create_server()
    print("✓ MCP server created successfully!", file=sys.stderr)
    return mcp

def main():
    """Main entry point when running as a script."""
    server = initialize_server()
    if server:
        print("Starting MCP server...", file=sys.stderr)
        
        transport_env = os.getenv("MCP_TRANSPORT", "stdio")
        port = int(os.getenv("MCP_PORT", "8000"))
        host = os.getenv("MCP_HOST", "127.0.0.1")
        
        valid_transports = ["stdio", "sse", "streamable-http"]
        if transport_env not in valid_transports:
            transport = cast(Literal["stdio", "sse", "streamable-http"], "stdio")
        else:
            transport = cast(Literal["stdio", "sse", "streamable-http"], transport_env)
        
        if transport == "stdio":
            server.run()
        else:
            server.run(
                transport=transport,
                port=port,
                host=host
            )

if __name__ == "__main__":
    main()