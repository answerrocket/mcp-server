"""Type definitions and models for the MCP server."""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from answer_rocket.graphql.schema import MaxCopilot, MaxCopilotSkill, MaxCopilotSkillParameter


@dataclass
class SkillParameter:
    """Processed skill parameter for MCP tool generation."""
    name: str
    type_hint: type
    description: Optional[str]
    required: bool
    is_multi: bool
    constrained_values: Optional[List[str]]
    
    @classmethod
    def from_max_parameter(cls, param: MaxCopilotSkillParameter) -> Optional['SkillParameter']:
        """Create SkillParameter from MaxCopilotSkillParameter."""
        # Only process CHAT parameters
        copilot_parameter_type = getattr(param, 'copilot_parameter_type', None)
        if copilot_parameter_type != "CHAT":
            return None
            
        param_name = str(param.name)
        
        # Determine parameter type based on is_multi field
        is_multi = bool(getattr(param, 'is_multi', False))
        type_hint = List[str] if is_multi else str
        
        # Get description from llm_description or description field
        description = str(getattr(param, 'llm_description', '') or 
                         getattr(param, 'description', '') or 
                         f"Parameter {param_name}")
        
        # Get constrained values if they exist
        constrained_values = getattr(param, 'constrained_values', None)
        if constrained_values:
            # Convert to list of strings
            if isinstance(constrained_values, list):
                constrained_values = [str(v) for v in constrained_values]
            else:
                constrained_values = None
                
        # Parameters are not required by default in the original code
        required = False
        
        return cls(
            name=param_name,
            type_hint=type_hint,
            description=description,
            required=required,
            is_multi=is_multi,
            constrained_values=constrained_values
        )


@dataclass
class SkillConfig:
    """Configuration for a skill tool."""
    skill: MaxCopilotSkill
    parameters: List[SkillParameter]
    
    @property
    def skill_id(self) -> str:
        """Get the skill ID."""
        return str(self.skill.copilot_skill_id)
    
    @property
    def skill_name(self) -> str:
        """Get the skill name."""
        return str(self.skill.name)
    
    @property
    def tool_name(self) -> str:
        """Generate MCP tool name from skill name."""
        # Create a safe tool name (alphanumeric and underscores only)
        safe_name = "".join(c if c.isalnum() or c == '_' else '_' for c in self.skill_name.lower())
        return safe_name.strip('_') or f"skill_{self.skill_id}"
    
    @property
    def tool_description(self) -> str:
        """Get tool description."""
        return str(self.skill.description or self.skill.detailed_description or f"Execute {self.skill_name} skill")
    
    @property
    def detailed_description(self) -> str:
        """Get detailed description for logging."""
        return str(self.skill.detailed_description) or self.tool_description
    
    @property
    def detailed_name(self) -> str:
        """Get detailed name if available."""
        return str(getattr(self.skill, 'detailed_name', self.skill_name))
    
    @property
    def is_scheduling_only(self) -> bool:
        """Check if skill is scheduling only."""
        return bool(getattr(self.skill, 'scheduling_only', False))
    
    def get_parameters_dict(self) -> Dict[str, Dict[str, Any]]:
        """Get parameters as a dictionary matching the original format."""
        parameters = {}
        for param in self.parameters:
            param_desc = param.description or f"Parameter {param.name}"
            if param.constrained_values:
                param_desc += f" (Allowed values: {', '.join(param.constrained_values)})"
                
            parameters[param.name] = {
                'type': 'array' if param.is_multi else 'string',
                'description': param_desc,
                'required': param.required,
                'is_multi': param.is_multi,
                'constrained_values': param.constrained_values
            }
        return parameters