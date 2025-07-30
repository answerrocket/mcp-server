"""Tool registry for managing MCP tools."""

import asyncio
import logging
from typing import List, Optional, Callable
from mcp.server import FastMCP

from mcp_server.skill_parameter import HydratedSkillConfig
from mcp_server.utils import ToolFactory, SkillService, RequestContextExtractor, ClientManager
from answer_rocket.client import AnswerRocketClient

class ToolRegistry:
    """Manages dynamic registration of skills as MCP tools.
    
    Tools are registered on-demand during each list_tools() call,
    supporting both context-based (remote) and static (local) copilot resolution.
    """
    
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
        self._original_list_tools = None
    
    def register_skills(self, skill_configs: List[HydratedSkillConfig]):
        """Register multiple skills as MCP tools."""
        for skill_config in skill_configs:
            try:
                self.register_skill(skill_config)
            except Exception as e:
                logging.error(f"Failed to register skill {skill_config.skill_name}: {e}")
    
    def register_skill(self, skill_config: HydratedSkillConfig):
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
            annotations=annotations,
            structured_output=True
        )

        logging.debug(f"Registered tool: {skill_config.tool_name}")
    
    def setup_dynamic_registration(self):
        """Set up dynamic tool registration."""
        self._original_list_tools = self.mcp.list_tools
        
        async def dynamic_list_tools():
            """Dynamically register tools based on context or static copilot ID."""
            if not self.mcp:
                return []
            
            self.clear_tools()
            
            copilot_id = self._resolve_copilot_id()
            
            if not copilot_id:
                logging.error("No copilot_id available for tool registration")
                return await self._original_list_tools()
            
            await self._register_dynamic_tools(copilot_id)
            
            return await self._original_list_tools()
        
        self.mcp._mcp_server.list_tools()(dynamic_list_tools)
    
    def _resolve_copilot_id(self) -> Optional[str]:
        """Resolve copilot ID from request context or static configuration."""
        # in remote mode, we get the copilot id from the request context
        context = self.mcp.get_context()
        if context:
            copilot_id = RequestContextExtractor.extract_copilot_id(context)
            if copilot_id:
                return copilot_id
        # in local mode, we use the copilot id from the static configuration
        return self.copilot_id
    

    async def _register_dynamic_tools(self, copilot_id: str):
        """Register tools dynamically for a specific copilot."""
        context = self.mcp.get_context()

        if context:
            ar_url = str(context.request_context.request.base_url).rstrip("/")
            client = ClientManager.create_client_from_context(context, ar_url)
        else:
            if not self.ar_token:
                logging.error("AR token required for tool registration")
                return
            ar_url = self.ar_url
            client = AnswerRocketClient(ar_url, self.ar_token)
        
        if not client:
            logging.error("Failed to create AnswerRocket client")
            return
        
        skill_configs = SkillService.fetch_hydrated_reports(client, copilot_id)
        
        if skill_configs:
            temp_registry = ToolRegistry(
                mcp=self.mcp, 
                ar_url=ar_url,
                ar_token=self.ar_token,
                copilot_id=copilot_id
            )
            temp_registry.register_skills(skill_configs)
            

            logging.info(f"Registered {len(skill_configs)} skills for copilot {copilot_id}")
        else:
            logging.warning(f"No skills found for copilot {copilot_id}")
    

    async def send_tool_list_changed(self):
        """Send tool list changed notification."""
        context = self.mcp.get_context()
        if context and context._request_context:
            await context.session.send_tool_list_changed()
            logging.debug("Sent tool list changed notification")
    
    def clear_tools(self):
        """Clear all registered tools."""
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
            self.mcp._tool_manager._tools.clear()
            logging.debug("Cleared all tools from registry")