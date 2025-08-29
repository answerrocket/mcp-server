"""Type definitions and models for the MCP server."""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from uuid import UUID

from answer_rocket.config import HydratedReport


@dataclass
class SkillParameter:
    """Processed skill parameter for MCP tool generation."""
    name: str
    type_hint: type
    description: Optional[str]
    required: bool
    is_multi: bool
    metadata_field: str
    constrained_values: Optional[List[str]]
    
    @classmethod
    def from_hydrated_parameter(cls, param_dict: Dict[str, Any]) -> Optional['SkillParameter']:
        """Create SkillParameter from hydrated report parameter."""
        if param_dict['is_hidden']:
            return None
            
        param_name = param_dict['key']
        if not param_name:
            return None

        is_multi = param_dict['is_multi']

        metadata_field = param_dict['metadata_field']

        type_hint = List[str] if is_multi else str

        description = param_dict['llm_description'] or param_dict['description'] or f"Parameter {param_name}"

        constrained_values = param_dict['constrained_values']
        if constrained_values:
            if isinstance(constrained_values, list):
                constrained_values = [str(v) for v in constrained_values]
            else:
                constrained_values = None

        required = False
        
        return cls(
            name=param_name,
            type_hint=type_hint,
            description=description,
            required=required,
            is_multi=is_multi,
            metadata_field=metadata_field,
            constrained_values=constrained_values
        )

@dataclass
class HydratedSkillConfig:
    """Configuration for a skill tool from hydrated reports."""
    copilot_skill_id: str
    name: str
    tool_description: str
    detailed_description: str
    tool_name: str
    scheduling_only: bool
    dataset_id: Optional[UUID]
    parameters: List[SkillParameter]
    
    @classmethod
    def from_hydrated_report(cls, report: HydratedReport) -> Optional['HydratedSkillConfig']:
        """Create HydratedSkillConfig from hydrated report."""
        try:
            copilot_skill_id = report.copilot_skill_id
            name = report.name
            tool_description = report.tool_description
            detailed_description = report.detailed_description
            scheduling_only = report.scheduling_only
            
            # Skip scheduling-only skills
            if scheduling_only:
                return None
            
            # Generate tool name from skill name
            safe_name = "".join(c if c.isalnum() or c == '_' else '_' for c in name.lower())
            tool_name = safe_name.strip('_') or f"skill_{copilot_skill_id}"
            
            # Parse dataset ID
            dataset_id = None
            if report.dataset_id:
                try:
                    dataset_id = UUID(str(report.dataset_id))
                except (ValueError, TypeError):
                    pass
            
            # Process parameters
            parameters = []
            param_list = report.parameters

            for param_dict in param_list:
                skill_param = SkillParameter.from_hydrated_parameter(param_dict)
                if skill_param:
                    parameters.append(skill_param)
            
            return cls(
                copilot_skill_id=copilot_skill_id,
                name=name,
                tool_description=tool_description,
                detailed_description=detailed_description,
                tool_name=tool_name,
                scheduling_only=scheduling_only,
                dataset_id=dataset_id,
                parameters=parameters,
            )
        except Exception as e:
            import logging
            logging.error(f"Error creating HydratedSkillConfig from report: {e}")
            return None
    
    @property
    def skill_name(self) -> str:
        """Get the skill name."""
        return self.name
    
    @property
    def is_scheduling_only(self) -> bool:
        """Check if skill is scheduling only."""
        return self.scheduling_only
    
    @property
    def detailed_name(self) -> str:
        """Get detailed name (fallback to name since detailed_name not in hydrated reports)."""
        return self.name