"""MCP tool creation and management utilities."""

import inspect
from typing import Any, Callable, Optional
from mcp.types import ToolAnnotations
from mcp.server.fastmcp.server import Context

from mcp_server.models import SkillConfig
from .context import RequestContextExtractor
from .client import ClientManager


class ToolFactory:
    """Creates MCP tools and annotations."""
    
    @staticmethod
    def create_tool_annotations(skill_config: SkillConfig) -> ToolAnnotations:
        """Create ToolAnnotations for a skill."""
        return ToolAnnotations(
            title=skill_config.detailed_name,
            # Most copilot skills are read-only queries
            readOnlyHint=not skill_config.is_scheduling_only,
            # Skills are typically non-destructive
            destructiveHint=False,
            # Skills with same params should return same results
            idempotentHint=True,
            # Skills may interact with external data sources
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
        skill_parameters = skill_config.get_parameters_dict()
        
        async def skill_tool_function(context: Context, **kwargs):
            """Execute this AnswerRocket skill."""
            try:
                await context.info(f"Executing skill: {skill_config.skill_name}")
                
                # Validate and transform parameters
                processed_params = {}
                for param_name, param_info in skill_parameters.items():
                    if param_name in kwargs:
                        value = kwargs[param_name]
                        # if the value is null, don't include it in the processed_params
                        if value is None:
                            continue
                        processed_params[param_name] = value
                    elif param_info.get('required', False):
                        error_msg = f"Required parameter '{param_name}' not provided"
                        await context.error(error_msg)
                        return {
                            "success": False,
                            "error": error_msg,
                            "skill_name": skill_config.skill_name,
                            "skill_id": skill_config.skill_id
                        }
                
                if processed_params:
                    await context.debug(f"Using parameters: {processed_params}")
                
                # Create AnswerRocket client (supporting both local and remote modes)
                await context.info("Connecting to AnswerRocket...")
                ar_client = ClientManager.create_client_from_context(context, ar_url, ar_token)
                if not ar_client:
                    raise ValueError("Cannot create AnswerRocket client - no valid token available")
                
                if not ar_client.can_connect():
                    raise ValueError("Cannot connect to AnswerRocket")
                
                # Get copilot ID (for remote mode)
                actual_copilot_id = copilot_id or RequestContextExtractor.extract_copilot_id(context)
                if not actual_copilot_id:
                    raise ValueError("No copilot ID available")
                
                # Run the skill with processed parameters
                await context.info("Running skill...")
                skill_result = ar_client.skill.run(actual_copilot_id, skill_config.skill_name, processed_params)
                
                if not skill_result.success:
                    await context.error(f"Skill execution failed: {skill_result.error}")
                    return skill_result.error

                await context.info("Skill executed successfully")
                
                if skill_result.data is not None:
                    return skill_result.data.get("final_message", "")
                else:
                    return "No data returned from skill"
            except Exception as e:
                error_msg = f"Error running skill {skill_config.skill_name}: {str(e)}"
                await context.error(error_msg)
                return error_msg
        
        # Set function metadata
        skill_tool_function.__name__ = f"skill_{skill_config.tool_name}"
        skill_tool_function.__doc__ = skill_config.tool_description
        
        # Add parameter annotations for better MCP integration
        sig_params = []
        annotations = {}
        
        # Add context parameter first
        sig_params.append(
            inspect.Parameter(
                "context",
                inspect.Parameter.KEYWORD_ONLY,
                annotation=Context
            )
        )
        annotations["context"] = Context
        
        for param in skill_config.parameters:
            is_required = param.required
            param_type = param.type_hint if is_required else Optional[param.type_hint]
            default = inspect.Parameter.empty if is_required else None
            
            sig_params.append(
                inspect.Parameter(
                    param.name,
                    inspect.Parameter.KEYWORD_ONLY,
                    default=default,
                    annotation=param_type
                )
            )
            # Also add to annotations dict
            annotations[param.name] = param_type
        
        # Create proper function signature and annotations
        try:
            skill_tool_function.__signature__ = inspect.Signature(sig_params)
            skill_tool_function.__annotations__ = annotations
        except Exception as e:
            # Fallback to no signature
            skill_tool_function.__signature__ = None
            skill_tool_function.__annotations__ = {"context": Context}
        
        return skill_tool_function 