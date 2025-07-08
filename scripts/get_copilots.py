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
        
        # Extract basic copilot metadata (without detailed skill enumeration)
        copilot_list = []
        for copilot in copilots:            
            copilot_data = {
                "copilot_id": str(copilot.copilot_id),
                "name": copilot.name,
                "description": copilot.description,
                "skill_count": len(copilot.copilot_skill_ids)
            }
            copilot_list.append(copilot_data)
        
        # Output as JSON
        print(json.dumps(copilot_list, indent=2))
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main() 