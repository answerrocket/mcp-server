"""Skill-related operations and configurations."""

import logging
from typing import List
from answer_rocket.client import AnswerRocketClient

from mcp_server.skill_parameter import HydratedSkillConfig


class SkillService:
    """Handles skill-related operations and configurations."""
    
    @staticmethod
    def fetch_hydrated_reports(client: AnswerRocketClient, copilot_id: str, load_all_skills: bool = False) -> List[HydratedSkillConfig]:
        """Fetch hydrated reports for a copilot."""
        try:
            hydrated_reports = client.config.get_copilot_hydrated_reports(
                copilot_id=copilot_id,
                load_all_skills=load_all_skills
            )
            
            if not hydrated_reports:
                logging.warning(f"No hydrated reports found for copilot {copilot_id}")
                return []
            
            skill_configs = []
            for report in hydrated_reports:
                skill_config = HydratedSkillConfig.from_hydrated_report(report)
                if skill_config:
                    skill_configs.append(skill_config)
            
            logging.info(f"Processed {len(skill_configs)} skills from hydrated reports for copilot {copilot_id}")
            return skill_configs
        
        except Exception as e:
            logging.error(f"Error fetching hydrated reports for copilot {copilot_id}: {e}")
            return []