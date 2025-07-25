"""Centralized configuration management for the MCP server."""

import os
from typing import Optional
from dataclasses import dataclass
import logging


@dataclass
class ServerConfig:
    """Configuration for the MCP server."""
    
    mode: str
    ar_url: Optional[str]  # Only used for local mode
    host: str
    port: int
    transport: str
    
    # Mode-specific fields
    ar_token: Optional[str] = None
    copilot_id: Optional[str] = None
    
    @classmethod
    def from_environment(cls) -> 'ServerConfig':
        """Create configuration from environment variables."""
        mode = os.getenv("MCP_MODE", "local").lower()
        
        if mode not in ["local", "remote"]:
            raise ValueError(f"Invalid MCP_MODE: {mode}. Must be 'local' or 'remote'")
        
        # Only get AR_URL for local mode
        ar_url = os.getenv("AR_URL") if mode == "local" else None
        
        transport = os.getenv("MCP_TRANSPORT", "stdio")
        
        if transport not in ["stdio", "streamable-http"]:
            raise ValueError(f"Invalid MCP_TRANSPORT: {transport}. Must be 'stdio' or 'streamable-http'")
        
        config = cls(
            mode=mode,
            ar_url=ar_url,
            host=os.getenv("MCP_HOST", "localhost"),
            port=int(os.getenv("MCP_PORT", "9090")),
            transport=transport,
        )
        
        if mode == "local":
            config.ar_token = os.getenv("AR_TOKEN")
            config.copilot_id = os.getenv("COPILOT_ID")
            config.validate_local_mode()
        else:
            config.validate_remote_mode()
            
        return config
    
    def validate_local_mode(self):
        """Validate configuration for local mode."""
        if not self.ar_url:
            raise ValueError("AR_URL environment variable is required for local mode")
        if not self.ar_token:
            raise ValueError("AR_TOKEN environment variable is required for local mode")
        if not self.copilot_id:
            raise ValueError("COPILOT_ID environment variable is required for local mode")
    
    def validate_remote_mode(self):
        """Validate configuration for remote mode."""
        # Remote mode requires no AR_URL - everything is derived from request context
        logging.info("Remote mode: all URLs will be derived from request context")
    
    @property
    def auth_server_url(self) -> Optional[str]:
        """Get auth server URL - only available for local mode."""
        return self.ar_url if self.is_local else None
    
    @property
    def resource_server_url(self) -> str:
        """Get resource server URL for remote mode."""
        protocol = "http" if self.host in ["127.0.0.1", "localhost"] else "https"
        return f"{protocol}://{self.host}:{self.port}"
    
    @property
    def is_local(self) -> bool:
        """Check if running in local mode."""
        return self.mode == "local"
    
    @property
    def is_remote(self) -> bool:
        """Check if running in remote mode."""
        return self.mode == "remote"