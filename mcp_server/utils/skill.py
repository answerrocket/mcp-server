"""Skill-related operations and configurations."""

import asyncio
import logging
from typing import List, Optional
from answer_rocket.client import AnswerRocketClient
from answer_rocket.graphql.schema import MaxCopilot, MaxCopilotSkill

from mcp_server.skill_parameter import SkillConfig, SkillParameter


class SkillService:
    """Handles skill-related operations and configurations."""
    
    @staticmethod
    def extract_skill_parameters(skill: MaxCopilotSkill) -> List[SkillParameter]:
        """Extract parameters from a skill."""
        parameters = []
        
        if not hasattr(skill, 'parameters') or skill.parameters is None:
            return parameters
        
        for param in skill.parameters:
            skill_param = SkillParameter.from_max_parameter(param)
            if skill_param:
                parameters.append(skill_param)
                
        return parameters

    @staticmethod
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
            logging.error(f"Error fetching skill {skill_id}: {e}")
            return None

    @staticmethod
    async def build_skill_configs_async(copilot: MaxCopilot, client: AnswerRocketClient) -> List[SkillConfig]:
        """Build skill configurations for all skills in a copilot."""
        if not copilot.copilot_skill_ids:
            return []
            
        skill_ids = copilot.copilot_skill_ids
        if not isinstance(skill_ids, list):
            skill_ids = [skill_ids] if skill_ids else []
        
        skill_infos = await asyncio.gather(*[
            SkillService.fetch_skill_info(client, str(copilot.copilot_id), str(skill_id)) 
            for skill_id in skill_ids
        ])
        
        skill_configs = []
        for skill_info in skill_infos:
            if skill_info and not getattr(skill_info, 'scheduling_only', False):
                parameters = SkillService.extract_skill_parameters(skill_info)
                skill_config = SkillConfig(
                    skill=skill_info,
                    parameters=parameters
                )
                skill_configs.append(skill_config)
                
        return skill_configs

    @staticmethod
    def build_skill_configs(copilot: MaxCopilot, client: AnswerRocketClient) -> List[SkillConfig]:
        """Wrapper to run async skill config building."""
        try:
            asyncio.get_running_loop()
            raise RuntimeError("build_skill_configs() called from async context. Use build_skill_configs_async() instead.")
        except RuntimeError:
            return asyncio.run(SkillService.build_skill_configs_async(copilot, client))