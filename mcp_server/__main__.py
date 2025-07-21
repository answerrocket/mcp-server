"""MCP Server entry point for the AnswerRocket MCP server."""

import sys
import os
import logging
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
        
        logging.info(f"Mode: {mode}")
        logging.info(f"AR_URL: {ar_url}")
        logging.info(f"AR_TOKEN: {ar_token}")
        logging.info(f"COPILOT_ID: {copilot_id}")
        
        if not all([ar_url, ar_token, copilot_id]):
            logging.error("Error: Missing required environment variables for local mode")
            logging.error("Please set AR_URL, AR_TOKEN, and COPILOT_ID")
            return False
            
    elif mode == "remote":
        ar_url = os.getenv("AR_URL")
        mcp_host = os.getenv("MCP_HOST", "localhost")
        mcp_port = os.getenv("MCP_PORT", "9090")
        
        logging.info(f"Mode: {mode}")
        logging.info(f"AR_URL: {ar_url}")
        logging.info(f"MCP_HOST: {mcp_host}")
        logging.info(f"MCP_PORT: {mcp_port}")
        logging.info(f"AUTH_SERVER_URL: {ar_url} (derived from AR_URL)")
        

        protocol = "http" if mcp_host in ["127.0.0.1", "localhost"] else "https"
        resource_server_url = f"{protocol}://{mcp_host}:{mcp_port}"
        logging.info(f"RESOURCE_SERVER_URL: {resource_server_url} (derived from MCP_HOST:MCP_PORT)")
        
        if not ar_url:
            logging.error("Error: Missing required environment variable for remote mode")
            logging.error("Please set AR_URL")
            return False
    else:
        logging.error(f"Error: Unknown mode '{mode}'. Use 'local' or 'remote'")
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
    
    logging.info(f"Creating MCP server in {mode} mode...")
    try:
        mcp = create_server()
        logging.info("✓ MCP server created successfully!")
    except Exception as e:
        logging.error(f"Error creating MCP server: {e}")
        sys.exit(1)
    
    return mcp

def main():
    """Main entry point when running as a script."""
    # Configure logging to show INFO level messages
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s'
    )
    
    server = initialize_server()
    transport = cast(Literal["stdio", "sse", "streamable-http"], os.getenv("MCP_TRANSPORT", "stdio"))
    if server:
        logging.info(f"Running MCP server in {transport} mode...")
        server.run(transport=transport)

if __name__ == "__main__":
    main()