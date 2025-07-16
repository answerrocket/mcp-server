"""Utility functions for the MCP server."""

import os
import sys
import asyncio
import inspect
from typing import Any, Callable, Dict, List, Optional, Tuple
from answer_rocket.client import AnswerRocketClient
from answer_rocket.graphql.schema import MaxCopilot, MaxCopilotSkill
from mcp.types import ToolAnnotations
from mcp.server.fastmcp.server import Context

from mcp_server.models import SkillConfig, SkillParameter


def validate_environment() -> Tuple[str, str, str]:
    """Validate required environment variables."""
    ar_url = os.getenv("AR_URL")
    ar_token = os.getenv("AR_TOKEN")
    copilot_id = os.getenv("COPILOT_ID")
    
    if not ar_url:
        print("Error: AR_URL environment variable is required")
        sys.exit(1)
    if not ar_token:
        print("Error: AR_TOKEN environment variable is required")
        sys.exit(1)
    if not copilot_id:
        print("Error: COPILOT_ID environment variable is required")
        sys.exit(1)
        
    return ar_url, ar_token, copilot_id


def create_client(ar_url: str, ar_token: str) -> AnswerRocketClient:
    """Create and validate AnswerRocket client."""
    client = AnswerRocketClient(ar_url, ar_token)
    
    if not client.can_connect():
        print(f"Error: Cannot connect to AnswerRocket at {ar_url}")
        print("Please check your AR_URL and AR_TOKEN")
        sys.exit(1)
        
    return client


def get_copilot_info(client: AnswerRocketClient, copilot_id: str) -> Optional[MaxCopilot]:
    """Get copilot information including name and skills."""
    try:
        if not client.can_connect():
            raise ValueError("Cannot connect to AnswerRocket")
        
        # Get copilot information
        copilot_info = client.config.get_copilot(True, copilot_id)
        if not copilot_info:
            raise ValueError(f"Copilot with ID '{copilot_id}' not found")
        
        return copilot_info
    except Exception as e:
        print(f"Error getting copilot info: {e}")
        # Fallback to None
        return None


def extract_skill_parameters(skill: MaxCopilotSkill) -> List[SkillParameter]:
    """Extract parameters from a skill."""
    parameters = []
    
    if not hasattr(skill, 'parameters') or not skill.parameters:
        return parameters
        
    for param in skill.parameters:
        skill_param = SkillParameter.from_max_parameter(param)
        if skill_param:
            parameters.append(skill_param)
            
    return parameters


async def fetch_skill_info(client: AnswerRocketClient, copilot_id: str, skill_id: str) -> Optional[MaxCopilotSkill]:
    """Fetch skill information asynchronously."""
    try:
        skill_info = client.config.get_copilot_skill(
            copilot_id=copilot_id,
            copilot_skill_id=str(skill_id),
            use_published_version=True
        )
        return skill_info
    except Exception as e:
        print(f"❌ Error fetching skill {skill_id}: {e}")
        return None


async def build_skill_configs_async(copilot: MaxCopilot, client: AnswerRocketClient) -> List[SkillConfig]:
    """Build skill configurations for all skills in a copilot."""

    if not copilot.copilot_skill_ids:
        return []
        
    # Convert skill IDs to list
    skill_ids = copilot.copilot_skill_ids
    if not isinstance(skill_ids, list):
        skill_ids = [skill_ids] if skill_ids else []
    
    # Fetch all skill info in parallel
    skill_infos = await asyncio.gather(*[
        fetch_skill_info(client, str(copilot.copilot_id), str(skill_id)) 
        for skill_id in skill_ids
    ])
    
    # Build skill configs
    skill_configs = []
    for skill_info in skill_infos:
        if skill_info and not getattr(skill_info, 'scheduling_only', False):
            parameters = extract_skill_parameters(skill_info)
            skill_config = SkillConfig(
                skill=skill_info,
                parameters=parameters
            )
            skill_configs.append(skill_config)
            
    return skill_configs


def build_skill_configs(copilot: MaxCopilot, client: AnswerRocketClient) -> List[SkillConfig]:
    """Wrapper to run async skill config building."""
    return asyncio.run(build_skill_configs_async(copilot, client))


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


def create_skill_tool_function(
    skill_config: SkillConfig, 
    ar_url: str, 
    ar_token: str, 
    copilot_id: str
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
            
            # Create AnswerRocket client
            await context.info("Connecting to AnswerRocket...")
            ar_client = AnswerRocketClient(ar_url, ar_token)
            if not ar_client.can_connect():
                raise ValueError("Cannot connect to AnswerRocket")
            
            # Run the skill with processed parameters
            await context.info("Running skill...")
            skill_result = ar_client.skill.run(copilot_id, skill_config.skill_name, processed_params)
            
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


def validate_skill_arguments(args: Dict[str, Any], skill_config: SkillConfig) -> Dict[str, Any]:
    """Validate and process skill arguments."""
    validated_args = {}
    
    for param in skill_config.parameters:
        if param.name in args:
            value = args[param.name]
            
            # Skip None values
            if value is None:
                continue
                
            # Validate constrained values
            if param.constrained_values:
                if param.is_multi:
                    if not isinstance(value, list):
                        value = [value]
                    invalid_values = [v for v in value if v not in param.constrained_values]
                    if invalid_values:
                        raise ValueError(
                            f"Invalid values for {param.name}: {invalid_values}. "
                            f"Allowed values: {param.constrained_values}"
                        )
                else:
                    if value not in param.constrained_values:
                        raise ValueError(
                            f"Invalid value for {param.name}: {value}. "
                            f"Allowed values: {param.constrained_values}"
                        )
            
            # Handle multi-value parameters
            if param.is_multi and not isinstance(value, list):
                value = [value]
                
            validated_args[param.name] = value
        elif param.required:
            raise ValueError(f"Missing required parameter: {param.name}")
    
    return validated_args