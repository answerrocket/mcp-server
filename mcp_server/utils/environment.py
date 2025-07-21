"""Environment validation utilities."""

import os
import sys
import logging
from typing import Tuple


class EnvironmentValidator:
    """Handles environment variable validation for different modes."""
    
    @staticmethod
    def validate_local_environment() -> Tuple[str, str, str]:
        """Validate required environment variables for local mode."""
        ar_url = os.getenv("AR_URL")
        ar_token = os.getenv("AR_TOKEN")
        copilot_id = os.getenv("COPILOT_ID")
        
        if not ar_url:
            logging.error("Error: AR_URL environment variable is required")
            sys.exit(1)
        if not ar_token:
            logging.error("Error: AR_TOKEN environment variable is required")
            sys.exit(1)
        if not copilot_id:
            logging.error("Error: COPILOT_ID environment variable is required")
            sys.exit(1)
            
        return ar_url, ar_token, copilot_id

    @staticmethod
    def validate_remote_environment() -> Tuple[str, str, str]:
        """Validate required environment variables for remote mode."""
        ar_url = os.getenv("AR_URL")
        
        if not ar_url:
            logging.error("Error: AR_URL environment variable is required")
            sys.exit(1)
        
        # AUTH_SERVER_URL is the same as AR_URL (we are the OAuth server)
        auth_server_url = ar_url
        
        # RESOURCE_SERVER_URL is constructed from MCP_HOST and MCP_PORT
        mcp_host = os.getenv("MCP_HOST", "localhost")
        mcp_port = os.getenv("MCP_PORT", "9090")
        
        # Determine protocol - use https for non-localhost, http for localhost
        if mcp_host in ["127.0.0.1", "localhost"]:
            protocol = "http"
        else:
            protocol = "https"
        
        resource_server_url = f"{protocol}://{mcp_host}:{mcp_port}"
            
        return ar_url, auth_server_url, resource_server_url

    @staticmethod
    def get_mcp_mode() -> str:
        """Get the MCP mode (local or remote)."""
        return os.getenv("MCP_MODE", "local").lower() 