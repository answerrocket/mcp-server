"""Base mode handler for the MCP server."""

from abc import ABC, abstractmethod
from typing import Optional
from answer_rocket.client import AnswerRocketClient
from answer_rocket.graphql.schema import MaxCopilot

from mcp_server.config import ServerConfig
from mcp_server.auth.fastmcp_extended import FastMCPExtended


class BaseMode(ABC):
    """Abstract base class for mode handlers."""
    
    def __init__(self, config: ServerConfig):
        self.config = config
        self.mcp: Optional[FastMCPExtended] = None
        self.client: Optional[AnswerRocketClient] = None
        self.copilot: Optional[MaxCopilot] = None
    
    @abstractmethod
    def create_mcp_server(self) -> FastMCPExtended:
        """Create and configure the MCP server instance."""
        pass
    
    def setup_tools(self):
        """Set up dynamic tool registration for the MCP server using ToolRegistry.
        
        Default implementation that works for all modes.
        Tools are registered dynamically on each list_tools() call.
        """
        if not self.mcp:
            return

        from mcp_server.tool_registry import ToolRegistry
        
        registry = ToolRegistry(
            mcp=self.mcp,
            ar_url=self.config.ar_url,
            ar_token=getattr(self.config, 'ar_token', None),
            copilot_id=getattr(self.config, 'copilot_id', None)
        )
        
        registry.setup_dynamic_registration()
    
    def initialize(self) -> FastMCPExtended:
        """Initialize the mode handler and return configured MCP server."""
        self.mcp = self.create_mcp_server()
        self.setup_tools()
        return self.mcp