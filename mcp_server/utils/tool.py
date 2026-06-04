"""MCP tool creation and management utilities."""

import inspect
from typing import Callable, Optional, Dict, Any, Annotated
from mcp.types import ToolAnnotations
from mcp.server.fastmcp.server import Context
from pydantic import Field

from mcp_server.skill_parameter import HydratedSkillConfig
from .context import RequestContextExtractor
from .client import ClientManager
from .validation import ArgumentValidator


class ToolFactory:
    """Creates MCP tools and annotations."""
    
    @staticmethod
    def create_tool_annotations(skill_config: HydratedSkillConfig) -> ToolAnnotations:
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
        skill_config: HydratedSkillConfig, 
        ar_url: str, 
        ar_token: Optional[str] = None, 
        copilot_id: Optional[str] = None
    ) -> Callable:
        """Create a tool function for a skill with proper signature."""
        
        async def skill_tool_function(context: Context, **kwargs) -> str:
            """Execute this AnswerRocket skill."""
            try:
                processed_params = ArgumentValidator.validate_skill_arguments(kwargs, skill_config)
                
                client = ClientManager.create_client_from_context(context, ar_url, ar_token)
                if not client or not client.can_connect():
                    raise ValueError("Cannot connect to AnswerRocket")
                
                actual_copilot_id = copilot_id or RequestContextExtractor.extract_copilot_id(context)
                if not actual_copilot_id:
                    raise ValueError("No copilot ID available")
                
                await context.info(f"Executing skill: {skill_config.skill_name}")

                skill_result = client.skill.run(actual_copilot_id,
                                                skill_config.skill_name,
                                                processed_params,
                                                validate_parameters=True)
                
                if not skill_result.success:
                    error_msg = f"Skill execution failed: {skill_result.error}"
                    await context.error(error_msg)
                    return error_msg
                
                await context.info("Skill executed successfully")
                if skill_result.data:
                    return skill_result.data.get("final_message", "No message returned")
                return "No data returned from skill"
                
            except ValueError as e:
                error_msg = f"Parameter validation error: {str(e)}"
                await context.error(error_msg)
                return error_msg
            except Exception as e:
                error_msg = f"Error running skill {skill_config.skill_name}: {str(e)}"
                await context.error(error_msg)
                return error_msg
        
        ToolFactory._configure_function_metadata(skill_tool_function, skill_config)
        return skill_tool_function
    
    @staticmethod
    def _configure_function_metadata(func: Callable, skill_config: HydratedSkillConfig):
        """Configure function metadata and signature."""
        func.__name__ = f"skill_{skill_config.tool_name}"
        func.__doc__ = skill_config.tool_description
        
        sig_params = [
            inspect.Parameter("context", inspect.Parameter.KEYWORD_ONLY, annotation=Context)
        ]
        
        annotations: Dict[str, Any] = {"context": Context}
        
        for param in skill_config.parameters:
            base_type = param.type_hint
            field_info = Field(description=param.description or f"Parameter {param.name}")
            
            if param.constrained_values:
                field_info = Field(
                    description=param.description or f"Parameter {param.name}",
                    json_schema_extra={"enum": param.constrained_values}
                )
            
            annotated_type = Annotated[base_type, field_info]
            param_type = annotated_type if param.required else Optional[annotated_type]
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
        
        # Add return type annotation
        annotations["return"] = str
        
        try:
            func.__signature__ = inspect.Signature(sig_params, return_annotation=str)
            func.__annotations__ = annotations
        except Exception:
            func.__annotations__ = {"context": Context, "return": str}