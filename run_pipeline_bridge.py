"""
JSON Bridge interface for Node.js Express server to invoke Python Grievance AI Pipeline.
Receives JSON request via command-line argument or stdin and outputs standard JSON.
"""

import sys
import json
from pipeline import pipeline_instance

def main():
    pipeline_instance.initialize()
    
    if len(sys.argv) > 1:
        input_data = sys.argv[1]
    else:
        input_data = sys.stdin.read()
        
    if not input_data or not input_data.strip():
        print(json.dumps({"error": "Empty input"}))
        return

    try:
        payload = json.loads(input_data)
        text = payload.get("text", "")
        area = payload.get("area", "Unknown")
        days_open = payload.get("days_open", 0)

        result = pipeline_instance.process_grievance(text, area=area, days_open=days_open)
        print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"error": str(e)}))

if __name__ == "__main__":
    main()
