#!/usr/bin/env python3
"""
Script to get copilot metadata from AnswerRocket.
This is used by the install script to create multiple MCP servers.
"""

import sys
import json
import os
from answer_rocket import AnswerRocketClient


def main():
    """Get copilot metadata and output as JSON."""
    
    # Get credentials from command line args
    if len(sys.argv) != 3:
        print("Usage: python get_copilots.py <AR_URL> <AR_TOKEN>", file=sys.stderr)
        sys.exit(1)
    
    ar_url = sys.argv[1]
    ar_token = sys.argv[2]
    
    try:
        # Create AnswerRocket client
        ar_client = AnswerRocketClient(ar_url, ar_token)
        
        if not ar_client.can_connect():
            print("Error: Cannot connect to AnswerRocket", file=sys.stderr)
            sys.exit(1)
        
        # Get all copilots
        copilots = ar_client.config.get_copilots()
        
        if not copilots:
            print("Error: No copilots found", file=sys.stderr)
            sys.exit(1)
        
        # Extract copilot metadata
        copilot_list = []
        for copilot in copilots:
            copilot_data = {
                "copilot_id": copilot.copilot_id,
                "name": copilot.name,
                "description": copilot.description,
                "skill_ids": copilot.copilot_skill_ids or []
            }
            
            # Get skill details for each copilot
            skills = []
            for skill_id in copilot.copilot_skill_ids or []:
                try:
                    skill_info = ar_client.config.get_copilot_skill(True, copilot.copilot_id, skill_id)
                    if skill_info:
                        skills.append({
                            "skill_id": skill_info.copilot_skill_id,
                            "name": skill_info.name,
                            "detailed_name": skill_info.detailed_name,
                            "description": skill_info.description,
                            "detailed_description": skill_info.detailed_description,
                            "skill_type": skill_info.copilot_skill_type,
                            "dataset_id": skill_info.dataset_id,
                            "scheduling_only": skill_info.scheduling_only
                        })
                except Exception as e:
                    print(f"Warning: Could not get skill {skill_id} details: {e}", file=sys.stderr)
            
            copilot_data["skills"] = skills
            copilot_list.append(copilot_data)
        
        # Output as JSON
        print(json.dumps(copilot_list, indent=2))
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main() 