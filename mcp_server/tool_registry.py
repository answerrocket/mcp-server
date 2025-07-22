"""Tool registry for managing MCP tools."""

import logging
from typing import List, Optional, Callable
from mcp.server import FastMCP

from mcp_server.skill_parameter import SkillConfig
from mcp_server.utils import ToolFactory


class ToolRegistry:
    """Manages registration of skills as MCP tools."""
    
    def __init__(
        self, 
        mcp: FastMCP, 
        ar_url: str,
        ar_token: Optional[str] = None,
        copilot_id: Optional[str] = None
    ):
        self.mcp = mcp
        self.ar_url = ar_url
        self.ar_token = ar_token
        self.copilot_id = copilot_id
    
    def register_skills(self, skill_configs: List[SkillConfig]):
        """Register multiple skills as MCP tools."""
        for skill_config in skill_configs:
            try:
                self.register_skill(skill_config)
            except Exception as e:
                logging.error(f"Failed to register skill {skill_config.skill_name}: {e}")
    
    def register_skill(self, skill_config: SkillConfig):
        """Register a single skill as an MCP tool."""
        tool_func = ToolFactory.create_skill_tool_function(
            skill_config,
            self.ar_url,
            self.ar_token,
            self.copilot_id
        )
        
        annotations = ToolFactory.create_tool_annotations(skill_config)
        
        self.mcp.add_tool(
            tool_func,
            name=skill_config.tool_name,
            description=skill_config.detailed_description,
            annotations=annotations
        )
        
        logging.debug(f"Registered tool: {skill_config.tool_name}")
    
    def clear_tools(self):
        """Clear all registered tools."""
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
            self.mcp._tool_manager._tools.clear()