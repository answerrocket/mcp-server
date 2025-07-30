"""Argument validation utilities."""
import json
from typing import Any, Dict
from mcp_server.skill_parameter import HydratedSkillConfig


class ArgumentValidator:
    """Validates function arguments and parameters."""
    
    @staticmethod
    def validate_skill_arguments(args: Dict[str, Any], skill_config: HydratedSkillConfig) -> Dict[str, Any]:
        """Validate and process skill arguments with constraint checking."""
        validated_args = {}
        
        for param in skill_config.parameters:
            if param.name not in args:
                if param.required:
                    raise ValueError(f"Missing required parameter: {param.name}")
                continue
                
            value = args[param.name]
            if value is None:
                continue
            
            if param.constrained_values:
                ArgumentValidator._validate_constraints(param.name, value, param.constrained_values, param.is_multi)
            
            # Ensure multi-value parameters are lists
            if param.is_multi and not isinstance(value, list):
                value = [value]
                
            validated_args[param.name] = value
        
        return validated_args
    
    @staticmethod
    def _validate_constraints(param_name: str, value: Any, allowed_values: list, is_multi: bool):
        """Validate value against allowed constraints. Not really necessary with the good LLMs. They have enough
        context to infer.
        """
        if is_multi:
            values = value if isinstance(value, list) else [value]
            invalid = [v for v in values if v not in allowed_values]
            if invalid:
                raise ValueError(
                    f"Invalid values for {param_name}: {invalid}. "
                    f"Allowed values: {allowed_values}"
                )
        else:
            if value not in allowed_values:
                raise ValueError(
                    f"Invalid value for {param_name}: {value}. "
                    f"Allowed values: {allowed_values}"
                )