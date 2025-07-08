"""MCP Server implementation for AnswerRocket."""

import asyncio
import sys
from typing import List, Optional
from fastmcp import FastMCP
from fastmcp.tools.tool import Tool
from answer_rocket.client import AnswerRocketClient
from answer_rocket.graphql.schema import MaxCopilot

from .models import SkillConfig
from .utils import (
    validate_environment,
    create_client,
    get_copilot_info,
    build_skill_configs,
    create_tool_annotations,
    create_skill_tool_function
)


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
        print(f"Initializing MCP server for copilot: {self.copilot_id}", file=sys.stderr)
        
        # Create client and fetch copilot
        self.client = create_client(self.ar_url, self.ar_token)
        
        # Get copilot information
        self.copilot = get_copilot_info(self.client, self.copilot_id)
        if not self.copilot:
            raise ValueError(f"Copilot {self.copilot_id} not found")
        
        # Get copilot name for server
        copilot_name = str(self.copilot.name) if self.copilot.name else self.copilot_id
        print(f"Copilot name: {copilot_name}", file=sys.stderr)
            
        # Initialize MCP with copilot name
        self.mcp = FastMCP(copilot_name)
        
        # Build skill configurations
        print("Building skill configurations", file=sys.stderr)
        self.skill_configs = build_skill_configs(self.copilot, self.client)
        print(f"Built {len(self.skill_configs)} skill configurations", file=sys.stderr)
        
        # Register tools
        print("Registering tools", file=sys.stderr)
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
            
            # Create Tool object and add it
            tool = Tool.from_function(
                tool_func,
                name=skill_config.tool_name,
                description=skill_config.detailed_description,
                annotations=annotations
            )
            self.mcp.add_tool(tool)
            
            # Log parameter info
            param_count = len(skill_config.parameters)
            param_info = f" with {param_count} parameters" if param_count > 0 else ""
            print(f"Created tool for skill: {skill_config.skill_name} ({skill_config.tool_name}){param_info}", 
                  file=sys.stderr)
            
            if param_count > 0:
                for param in skill_config.parameters:
                    required_text = 'required' if param.required else 'optional'
                    constrained_text = f" [{', '.join(param.constrained_values)}]" if param.constrained_values else ""
                    print(f"   - {param.name}: {param.type_hint.__name__} ({required_text}){constrained_text}", 
                          file=sys.stderr)
            
            return True
        except Exception as e:
            import traceback
            print(traceback.format_exc(), file=sys.stderr)
            print(f"❌ Error registering tool for skill {skill_config.skill_name}: {e}", file=sys.stderr)
            return False
    
    def _register_tools(self):
        """Register all skill tools with MCP using async operations."""
        async def register_all():
            results = await asyncio.gather(*[
                self._register_skill_tool_async(skill_config) 
                for skill_config in self.skill_configs
            ])
            success_count = sum(1 for result in results if result)
            print(f"Successfully initialized {success_count}/{len(self.skill_configs)} skill tools", 
                  file=sys.stderr)
        
        asyncio.run(register_all())
    
    def _add_skill_description_tool(self):
        """Add the get_skill_description tool."""
        def get_skill_description(skill_id: str) -> Optional[str]:
            """Get the description of a skill."""
            try:
                skill_info = self.client.config.get_copilot_skill(
                    copilot_id=self.copilot_id,
                    copilot_skill_id=str(skill_id),
                    use_published_version=True
                )
                if skill_info:
                    return str(skill_info.description or skill_info.detailed_description or 
                             f"No description available for skill {skill_id}")
                return None
            except Exception as e:
                print(f"Error getting skill description for {skill_id}: {e}", file=sys.stderr)
                return None
        
        # Create Tool object and add it
        tool = Tool.from_function(
            get_skill_description,
            name="get_skill_description",
            description="Get the description of a skill."
        )
        self.mcp.add_tool(tool)


def create_server() -> FastMCP:
    """Create and initialize the MCP server."""
    print("Creating MCP server", file=sys.stderr)
    ar_url, ar_token, copilot_id = validate_environment()
    server = AnswerRocketMCPServer(ar_url, ar_token, copilot_id)
    return server.initialize()