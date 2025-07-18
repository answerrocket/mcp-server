"""MCP Server implementation for AnswerRocket."""

import asyncio
import sys
import os
from typing import List, Optional
from pydantic import AnyHttpUrl
from starlette.requests import Request
from starlette.responses import Response
from answer_rocket.client import AnswerRocketClient
from answer_rocket.graphql.schema import MaxCopilot
from mcp_server.auth.token_verifier import IntrospectionTokenVerifier
from mcp.server import FastMCP
from mcp.server.auth.settings import AuthSettings
from mcp.server.fastmcp.server import Context
from mcp_server.models import SkillConfig
from mcp_server.utils import (
    EnvironmentValidator,
    ClientManager,
    CopilotService,
    SkillService,
    ToolFactory,
    RequestContextExtractor,
)


class AnswerRocketMCPServer:
    """MCP Server for AnswerRocket copilots."""
    
    def __init__(self, mode: str = "local"):
        self.mode = mode.lower()
        self.ar_url: Optional[str] = None
        self.ar_token: Optional[str] = None
        self.copilot_id: Optional[str] = None
        self.auth_server_url: Optional[str] = None
        self.resource_server_url: Optional[str] = None
        self.client: Optional[AnswerRocketClient] = None
        self.copilot: Optional[MaxCopilot] = None
        self.mcp: Optional[FastMCP] = None
        self.skill_configs: List[SkillConfig] = []
        
    def initialize(self) -> FastMCP:
        """Initialize the MCP server based on mode."""
        if self.mode == "local":
            return self._initialize_local()
        elif self.mode == "remote":
            return self._initialize_remote()
        else:
            raise ValueError(f"Unknown mode: {self.mode}")
    
    def _initialize_local(self) -> FastMCP:
        """Initialize the MCP server for local mode."""
        # Validate local environment
        self.ar_url, self.ar_token, self.copilot_id = EnvironmentValidator.validate_local_environment()
        
        # Create client and fetch copilot
        self.client = ClientManager.create_client(self.ar_url, self.ar_token)
        
        # Get copilot information
        self.copilot = CopilotService.get_copilot_info(self.client, self.copilot_id)
        if not self.copilot:
            raise ValueError(f"Copilot {self.copilot_id} not found")
        
        # Get copilot name for server
        copilot_name = str(self.copilot.name) if self.copilot.name else self.copilot_id
        
        port = int(os.getenv("MCP_PORT", "8000"))
        host = os.getenv("MCP_HOST", "127.0.0.1")
        
        # Initialize MCP without auth for local mode
        self.mcp = FastMCP(
            copilot_name,
            host=host,
            port=port
        )
        
        # Build skill configurations
        self.skill_configs = SkillService.build_skill_configs(self.copilot, self.client)
        
        # Register tools
        self._register_tools_local()
        
        return self.mcp
        
    def _initialize_remote(self) -> FastMCP:
        """Initialize the MCP server for remote mode with OAuth."""
        # Validate remote environment
        self.ar_url, self.auth_server_url, self.resource_server_url = EnvironmentValidator.validate_remote_environment()
        
        # Create token verifier for introspection with RFC 8707 resource validation
        token_verifier = IntrospectionTokenVerifier(
            introspection_endpoint=f"{self.auth_server_url}/api/oauth2/introspect",
            server_url=self.resource_server_url,
            validate_resource=True, 
        )

        port = int(os.getenv("MCP_PORT", "9090"))
        host = os.getenv("MCP_HOST", "localhost")
        
        # Initialize MCP with OAuth for remote mode
        self.mcp = FastMCP(
            "AnswerRocket MCP Server",
            token_verifier=token_verifier,
            auth=AuthSettings(
                issuer_url=AnyHttpUrl(self.auth_server_url),
                required_scopes=['read:copilots', 'read:copilotSkills', 'execute:copilotSkills', 'ping'],
                resource_server_url=AnyHttpUrl(self.resource_server_url),
            ),
            host=host,
            port=port
        )
        
        # Setup dynamic routing for remote mode
        self._setup_copilot_routing()
        
        # Setup dynamic tool registration
        self._setup_dynamic_tools()
        
        return self.mcp
    
    def _setup_copilot_routing(self):
        """Setup custom copilot routing that captures copilot ID and routes to MCP handler."""
        if not self.mcp:
            raise ValueError("MCP instance must be initialized before setting up routing")
        
        @self.mcp.custom_route("/mcp/copilot/{copilot_id:path}", methods=["GET", "POST", "OPTIONS", "DELETE"])
        async def handle_copilot_mcp(request: Request) -> Response:
            """Handle MCP requests for specific copilots."""
            # Extract copilot ID from the path
            copilot_id = request.path_params.get("copilot_id")
            
            # Store copilot metadata in request state for later use
            request.state.copilot_id = copilot_id
            request.state.copilot_metadata = {
                "copilot_id": copilot_id,
                "request_path": request.url.path,
                "original_path": "/mcp"
            }
            
            # Get the session manager
            if not self.mcp:
                return Response(status_code=500)
            session_manager = self.mcp.session_manager
            
            # Create a modified scope that appears to come from /mcp
            scope = dict(request.scope)
            scope["path"] = "/mcp"  # Rewrite path to /mcp
            scope["raw_path"] = b"/mcp"
            
            # Add copilot metadata to scope for access in tools
            scope.setdefault("state", {})["copilot_metadata"] = {
                "copilot_id": copilot_id,
                "original_path": request.url.path
            }
            
            # Delegate to the MCP session manager
            async def modified_receive():
                return await request.receive()
                
            async def modified_send(message):
                await request._send(message)  # type: ignore
                
            await session_manager.handle_request(scope, modified_receive, modified_send)
            return Response()
    
    def _setup_dynamic_tools(self):
        """Setup dynamic tool registration for remote mode."""
        if not self.mcp or not self.ar_url:
            raise ValueError("MCP instance and AR_URL must be initialized")
        
        # Store original list_tools method
        original_list_tools = self.mcp.list_tools
        
        async def dynamic_list_tools():
            """Dynamically register tools based on copilot ID from context."""
            if not self.mcp or not self.ar_url:
                print("Missing MCP or AR_URL in dynamic_list_tools", file=sys.stderr)
                return await original_list_tools()
                
            context = self.mcp.get_context()
            copilot_id = RequestContextExtractor.extract_copilot_id(context)
            
            print(f"Dynamic tools: copilot_id={copilot_id}", file=sys.stderr)
            
            # Always clear existing tools first
            self.mcp._tool_manager._tools.clear()
            
            if copilot_id:
                print(f"Getting copilot info for {copilot_id}", file=sys.stderr)
                # Get copilot info from context
                copilot = CopilotService.get_copilot_info_from_context(context, self.ar_url, copilot_id)
                
                if copilot:
                    print(f"Found copilot: {copilot.name}", file=sys.stderr)
                    # Create client from context
                    client = ClientManager.create_client_from_context(context, self.ar_url)
                    if client:
                        # Build and register skills for this copilot
                        skill_configs = await SkillService.build_skill_configs_async(copilot, client)
                        print(f"Found {len(skill_configs)} skills", file=sys.stderr)
                        for skill_config in skill_configs:
                            try:
                                tool_func = ToolFactory.create_skill_tool_function(
                                    skill_config, 
                                    self.ar_url
                                )
                                annotations = ToolFactory.create_tool_annotations(skill_config)
                                self.mcp.add_tool(
                                    tool_func,
                                    name=skill_config.tool_name,
                                    description=skill_config.detailed_description,
                                    annotations=annotations
                                )
                                print(f"Registered tool: {skill_config.tool_name}", file=sys.stderr)
                            except Exception as e:
                                # Skip failed tool registration
                                print(f"Failed to register tool for skill {skill_config.skill_name}: {e}", file=sys.stderr)
                    else:
                        print("Failed to create client from context", file=sys.stderr)
                else:
                    print(f"Copilot {copilot_id} not found", file=sys.stderr)
            else:
                print("No copilot_id found in context", file=sys.stderr)
            
            return await original_list_tools()
        
        # Replace the list_tools handler
        self.mcp._mcp_server.list_tools()(dynamic_list_tools)
    
    async def _register_skill_tool_async_local(self, skill_config: SkillConfig) -> bool:
        """Register a single skill as an MCP tool asynchronously for local mode."""
        try:
            # Validate required fields for local mode
            if not self.ar_url or not self.ar_token or not self.copilot_id:
                return False
                
            # Create tool function with proper signature for local mode
            tool_func = ToolFactory.create_skill_tool_function(
                skill_config, 
                self.ar_url, 
                self.ar_token, 
                self.copilot_id
            )
            
            # Create annotations
            annotations = ToolFactory.create_tool_annotations(skill_config)
            
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
    
    def _register_tools_local(self):
        """Register all skill tools with MCP using async operations for local mode."""
        async def register_all():
            results = await asyncio.gather(*[
                self._register_skill_tool_async_local(skill_config) 
                for skill_config in self.skill_configs
            ])
            success_count = sum(1 for result in results if result)
        
        asyncio.run(register_all())


def create_server() -> FastMCP:
    """Create and initialize the MCP server."""
    mode = EnvironmentValidator.get_mcp_mode()
    server = AnswerRocketMCPServer(mode)
    return server.initialize()