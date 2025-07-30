"""Monkeypatched version of FastMCP with starlette-context middleware support. We do this because the token verifier must point to the right place."""

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.routing import Mount, Route
from starlette_context.middleware import ContextMiddleware
from starlette_context.plugins import Plugin
from mcp.server import FastMCP

from mcp_server.auth.dynamic_auth_middleware import DynamicRequireAuthMiddleware


class BaseURLPlugin(Plugin):
    """Plugin to capture and store the base URL in starlette-context."""
    
    key = "base_url"
    
    async def process_request(self, request) -> str:
        """Extract base URL from the request."""
        return str(request.base_url)


class FastMCPExtended(FastMCP):
    """Extended FastMCP that includes starlette-context middleware."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # HACK: There's literally no better way to set the capabilities of the MCP server. Crazy.
        self._mcp_server.notification_options.tools_changed = True
        self._original_create_initialization_options = self._mcp_server.create_initialization_options
        self._mcp_server.create_initialization_options = self._create_initialization_options_with_notifications
        
    
    def _create_initialization_options_with_notifications(self, *args, **kwargs):
        """Create initialization options that include our notification settings."""
        return self._original_create_initialization_options(
            notification_options=self._mcp_server.notification_options,
            *args,
            **kwargs
        )
    
    def _add_context_middleware(self, middleware_list: list[Middleware]) -> list[Middleware]:
        """Add starlette-context middleware to the middleware list."""
        context_middleware_instance = Middleware(
            ContextMiddleware,
            plugins=[
                BaseURLPlugin()
            ]
        )
        
        return [context_middleware_instance] + middleware_list
    
    def _replace_require_auth_middleware_in_routes(self, routes):
        """Replace RequireAuthMiddleware with DynamicRequireAuthMiddleware in routes."""
        from mcp.server.auth.middleware.bearer_auth import RequireAuthMiddleware
        
        def replace_middleware(middleware_instance):
            """Helper to replace a RequireAuthMiddleware instance with our dynamic version."""
            if isinstance(middleware_instance, RequireAuthMiddleware):
                return DynamicRequireAuthMiddleware(
                    middleware_instance.app, 
                    middleware_instance.required_scopes
                )
            return middleware_instance
        
        new_routes = []
        for route in routes:
            if isinstance(route, Route):
                new_routes.append(Route(
                    route.path,
                    endpoint=replace_middleware(route.endpoint),
                    methods=route.methods,
                    name=route.name,
                    include_in_schema=route.include_in_schema
                ))
            elif isinstance(route, Mount):
                new_routes.append(Mount(
                    route.path,
                    app=replace_middleware(route.app),
                    name=route.name
                ))
            else:
                new_routes.append(route)
        
        return new_routes
    
    def _enhance_app_with_dynamic_middleware(self, original_app: Starlette) -> Starlette:
        """Common logic to enhance an app with dynamic auth middleware and context middleware."""
        # HACK: Replace RequireAuthMiddleware with our DynamicRequireAuthMiddleware in routes
        new_routes = self._replace_require_auth_middleware_in_routes(original_app.routes)
        
        # HACK: Add context middleware to the existing middleware
        new_middleware = self._add_context_middleware(list(original_app.user_middleware))
        
        # HACK: Create a new Starlette app with the modified routes and middleware
        return Starlette(
            debug=original_app.debug,
            routes=new_routes,
            middleware=new_middleware,
            exception_handlers=original_app.exception_handlers
        )

    def streamable_http_app(self) -> Starlette:
        """Return an instance of the StreamableHTTP server app with custom middleware."""
        original_app = super().streamable_http_app()
        app = self._enhance_app_with_dynamic_middleware(original_app)
        
        app.router.lifespan_context = lambda app: self.session_manager.run()
        
        return app

    async def run_streamable_http_async(self) -> None:
        """Run the server using StreamableHTTP transport with custom uvicorn config."""
        import uvicorn

        starlette_app = self.streamable_http_app()

        config = uvicorn.Config(
            app=starlette_app,
            host=self.settings.host,
            port=self.settings.port,
            log_level=self.settings.log_level.lower(),
            proxy_headers=True,
            forwarded_allow_ips="*"
        )
        server = uvicorn.Server(config)
        await server.serve()