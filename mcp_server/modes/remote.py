"""Remote mode handler for the MCP server."""

import logging
from pydantic import AnyHttpUrl
from mcp.server.auth.settings import AuthSettings

from mcp_server.auth.token_verifier import IntrospectionTokenVerifier
from mcp_server.modes.base import BaseMode
from mcp_server.tool_registry import ToolRegistry
from mcp_server.utils import RequestContextExtractor, CopilotService, SkillService, ClientManager, FastMCPExtended


class RemoteMode(BaseMode):
    """Handler for remote mode with OAuth authentication."""
    
    def create_mcp_server(self) -> FastMCPExtended:
        """Create MCP server for remote mode with OAuth."""
        token_verifier = IntrospectionTokenVerifier(
            validate_resource=True,
        )
        
        # Create MCP server with OAuth and support for our multi-tenant architecture
        # The MCP server will accept connections at /mcp/agent/{copilot_id}
        return FastMCPExtended(
            "AnswerRocket MCP Server",
            token_verifier=token_verifier,
            auth=AuthSettings(
                issuer_url=AnyHttpUrl("http://localhost"), # Placeholder - real URLs come from request context
                # I have verified that removing the issuer_url doesn't have any security implications
                # It only is responsible for creating the /.well-known/oauth-protected-resource which we don't use
                required_scopes=['read:copilots', 'read:copilotSkills', 'execute:copilotSkills', 'ping'],
                resource_server_url=None
                # I have verified that the resource_server_url doesn't have any security implications
                # It only is responsible for creating the /.well-known/oauth-protected-resource which we don't use
            ),
            host=self.config.host,
            port=self.config.port,
        )
    
    def setup_tools(self):
        """Set up dynamic tool registration for remote mode."""
        if not self.mcp:
            return
        
        self._setup_dynamic_tool_registration()
    
    def _setup_dynamic_tool_registration(self):
        """Set up dynamic tool registration based on request context."""
        if not self.mcp:
            return
            
        original_list_tools = self.mcp.list_tools
        
        async def dynamic_list_tools():
            """Dynamically register tools based on copilot ID from context."""
            if not self.mcp:
                return []
                
            context = self.mcp.get_context()
            copilot_id = RequestContextExtractor.extract_copilot_id(context)
            
            if not copilot_id:
                logging.error("No copilot_id found in context - invalid URL pattern")
                return await original_list_tools()

            self.mcp._tool_manager._tools.clear()
            

            await self._register_copilot_tools(context, copilot_id)
            
            return await original_list_tools()
        

        self.mcp._mcp_server.list_tools()(dynamic_list_tools)
    
    async def _register_copilot_tools(self, context, copilot_id: str):
        """Register tools for a specific copilot."""
        if not self.mcp:  # Type guard
            return

        ar_url = str(context.request_context.request.base_url).rstrip("/")

        copilot = CopilotService.get_copilot_info_from_context(
            context, ar_url, copilot_id
        )
        
        if not copilot:
            logging.error(f"Copilot {copilot_id} not found")
            return

        client = ClientManager.create_client_from_context(context, ar_url)
        if not client:
            logging.error("Failed to create client from context")
            return

        skill_configs = await SkillService.build_skill_configs_async(copilot, client)

        registry = ToolRegistry(mcp=self.mcp, ar_url=ar_url)
        registry.register_skills(skill_configs)
        
        logging.info(f"Registered {len(skill_configs)} skills for copilot {copilot.name}")