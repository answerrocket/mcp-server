"""MCP Server implementation for AnswerRocket."""

import asyncio
import sys
from typing import List, Optional
from pydantic import AnyHttpUrl
from answer_rocket.client import AnswerRocketClient
from answer_rocket.graphql.schema import MaxCopilot

from mcp_server.auth.token_verifier import IntrospectionTokenVerifier
from mcp.server import FastMCP
from mcp.server.auth.settings import AuthSettings
from mcp_server.models import SkillConfig
from mcp_server.utils import (
    build_skill_configs,
    create_client,
    create_skill_tool_function,
    create_tool_annotations,
    get_copilot_info,
    validate_environment,
)
import os

class AnswerRocketMCPServer:
    """MCP Server for AnswerRocket copilots."""
    
    def __init__(self, ar_url: str, ar_token: str, copilot_id: str):
        self.ar_url = ar_url
        self.ar_token = ar_token
        self.copilot_id = copilot_id
        self.client: Optional[AnswerRocketClient] = None
        self.copilot: Optional[MaxCopilot] = None
        self.mcp: Optional[FastMCP] = None
        self.skill_configs: List[SkillConfig] = []
        
    def initialize(self) -> FastMCP:
        """Initialize the MCP server."""
        
        # Create client and fetch copilot
        self.client = create_client(self.ar_url, self.ar_token)
        
        # Get copilot information
        self.copilot = get_copilot_info(self.client, self.copilot_id)
        if not self.copilot:
            raise ValueError(f"Copilot {self.copilot_id} not found")
        
        # Get copilot name for server
        copilot_name = str(self.copilot.name) if self.copilot.name else self.copilot_id
            
         # Create token verifier for introspection with RFC 8707 resource validation
        token_verifier = IntrospectionTokenVerifier(
            introspection_endpoint=f"{self.ar_url}/api/oauth2/introspect",
            server_url="http://localhost:9090",
            validate_resource=True, 
        )

        port = int(os.getenv("MCP_PORT", "8000"))
        host = os.getenv("MCP_HOST", "127.0.0.1")
        
        # Initialize MCP with copilot name
        self.mcp = FastMCP(
            copilot_name,
            token_verifier=token_verifier,
            auth=AuthSettings(
                issuer_url=AnyHttpUrl(f"{self.ar_url}"),
                required_scopes=["user"],
                resource_server_url=AnyHttpUrl("http://localhost:9090"),
            ),
            host=host,
            port=port
        )
        
        # Build skill configurations
        self.skill_configs = build_skill_configs(self.copilot, self.client)
        
        # Register tools
        self._register_tools()
        
        # Add get_skill_description tool
        self._add_skill_description_tool()
        
        return self.mcp
        
    async def _register_skill_tool_async(self, skill_config: SkillConfig) -> bool:
        """Register a single skill as an MCP tool asynchronously."""
        try:
            # Create tool function with proper signature
            tool_func = create_skill_tool_function(
                skill_config, 
                self.ar_url, 
                self.ar_token, 
                self.copilot_id
            )
            
            # Create annotations
            annotations = create_tool_annotations(skill_config)
            
            # Add tool directly to MCP
            assert self.mcp is not None, "MCP instance should be initialized"
            self.mcp.add_tool(
                tool_func,
                name=skill_config.tool_name,
                description=skill_config.detailed_description,
                annotations=annotations
            )
            return True
        except Exception as e:

            return False
    
    def _register_tools(self):
        """Register all skill tools with MCP using async operations."""
        async def register_all():
            results = await asyncio.gather(*[
                self._register_skill_tool_async(skill_config) 
                for skill_config in self.skill_configs
            ])
            success_count = sum(1 for result in results if result)
        
        asyncio.run(register_all())
    
    def _add_skill_description_tool(self):
        """Add the get_skill_description tool."""
        async def get_skill_description(context, skill_id: str) -> Optional[str]:
            """Get the description of a skill."""
            try:
                await context.info(f"Getting description for skill: {skill_id}")
                assert self.client is not None, "Client should be initialized"
                skill_info = self.client.config.get_copilot_skill(
                    copilot_id=self.copilot_id,
                    copilot_skill_id=str(skill_id),
                    use_published_version=True
                )
                if skill_info:
                    description = str(skill_info.description or skill_info.detailed_description or 
                                   f"No description available for skill {skill_id}")
                    await context.info("Successfully retrieved skill description")
                    return description
                await context.warning(f"No skill found with ID: {skill_id}")
                return None
            except Exception as e:
                error_msg = f"Error getting skill description for {skill_id}: {e}"
                await context.error(error_msg)
                return None
        
        # Add tool directly to MCP
        assert self.mcp is not None, "MCP instance should be initialized"
        self.mcp.add_tool(
            get_skill_description,
            name="get_skill_description",
            description="Get the description of a skill."
        )


def create_server() -> FastMCP:
    """Create and initialize the MCP server."""
    ar_url, ar_token, copilot_id = validate_environment()
    server = AnswerRocketMCPServer(ar_url, ar_token, copilot_id)
    return server.initialize()