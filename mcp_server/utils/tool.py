"""MCP tool creation and management utilities."""

import inspect
from typing import Callable, Optional
from mcp.types import ToolAnnotations
from mcp.server.fastmcp.server import Context

from mcp_server.skill_parameter import SkillConfig
from .context import RequestContextExtractor
from .client import ClientManager
from .validation import ArgumentValidator


class ToolFactory:
    """Creates MCP tools and annotations."""
    
    @staticmethod
    def create_tool_annotations(skill_config: SkillConfig) -> ToolAnnotations:
        """Create ToolAnnotations for a skill."""
        return ToolAnnotations(
            title=skill_config.detailed_name,
            readOnlyHint=not skill_config.is_scheduling_only,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=True
        )

    @staticmethod
    def create_skill_tool_function(
        skill_config: SkillConfig, 
        ar_url: str, 
        ar_token: Optional[str] = None, 
        copilot_id: Optional[str] = None
    ) -> Callable:
        """Create a tool function for a skill with proper signature."""
        
        async def skill_tool_function(context: Context, **kwargs):
            """Execute this AnswerRocket skill."""
            try:
                # Validate parameters using ArgumentValidator
                processed_params = ArgumentValidator.validate_skill_arguments(kwargs, skill_config)
                
                # Get client and copilot ID
                client = ClientManager.create_client_from_context(context, ar_url, ar_token)
                if not client or not client.can_connect():
                    raise ValueError("Cannot connect to AnswerRocket")
                
                actual_copilot_id = copilot_id or RequestContextExtractor.extract_copilot_id(context)
                if not actual_copilot_id:
                    raise ValueError("No copilot ID available")
                
                # Execute skill
                await context.info(f"Executing skill: {skill_config.skill_name}")
                skill_result = client.skill.run(actual_copilot_id, skill_config.skill_name, processed_params)
                
                if not skill_result.success:
                    error_msg = f"Skill execution failed: {skill_result.error}"
                    await context.error(error_msg)
                    return error_msg
                
                # Return result
                await context.info("Skill executed successfully")
                if skill_result.data:
                    return skill_result.data.get("final_message", "No message returned")
                return "No data returned from skill"
                
            except ValueError as e:
                # Handle validation errors
                error_msg = f"Parameter validation error: {str(e)}"
                await context.error(error_msg)
                return error_msg
            except Exception as e:
                error_msg = f"Error running skill {skill_config.skill_name}: {str(e)}"
                await context.error(error_msg)
                return error_msg
        
        # Set function metadata and signature
        ToolFactory._configure_function_metadata(skill_tool_function, skill_config)
        return skill_tool_function
    
    @staticmethod
    def _configure_function_metadata(func: Callable, skill_config: SkillConfig):
        """Configure function metadata and signature."""
        func.__name__ = f"skill_{skill_config.tool_name}"
        func.__doc__ = skill_config.tool_description
        
        # Build function signature
        sig_params = [
            inspect.Parameter("context", inspect.Parameter.KEYWORD_ONLY, annotation=Context)
        ]
        
        annotations = {"context": Context}
        
        for param in skill_config.parameters:
            param_type = param.type_hint if param.required else Optional[param.type_hint]
            default = inspect.Parameter.empty if param.required else None
            
            sig_params.append(
                inspect.Parameter(
                    param.name,
                    inspect.Parameter.KEYWORD_ONLY,
                    default=default,
                    annotation=param_type
                )
            )
            annotations[param.name] = param_type
        
        try:
            func.__signature__ = inspect.Signature(sig_params)
            func.__annotations__ = annotations
        except Exception:
            # Fallback for edge cases
            func.__annotations__ = {"context": Context}