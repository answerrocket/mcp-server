#!/usr/bin/env python3
"""
Validate AnswerRocket connection script.
"""

import sys
import os
from answer_rocket.client import AnswerRocketClient

def main():
    ar_url = os.environ.get('AR_URL')
    ar_token = os.environ.get('AR_TOKEN')
    
    if not ar_url or not ar_token:
        print("Error: AR_URL and AR_TOKEN environment variables must be set", file=sys.stderr)
        sys.exit(1)
    
    try:
        client = AnswerRocketClient(url=ar_url, token=ar_token)
        
        if not client.can_connect():
            print("Error: Failed to connect to AnswerRocket", file=sys.stderr)
            sys.exit(1)
        print('Connection successful')
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 