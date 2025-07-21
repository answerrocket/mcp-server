"""Argument validation utilities."""

from typing import Any, Dict

from mcp_server.skill_parameter import SkillConfig


class ArgumentValidator:
    """Validates function arguments and parameters."""
    
    @staticmethod
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