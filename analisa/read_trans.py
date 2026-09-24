import json
import sys

path = r'C:\Users\Acer\.gemini\antigravity-cli\brain\120edaaa-745a-4c0c-9fd8-f3834e71f89f\.system_generated\logs\transcript.jsonl'
with open(path, 'r', encoding='utf-8') as f:
    for line in f:
        s = json.loads(line)
        idx = s.get('step_index', 0)
        if 1350 <= idx <= 1430:
            content = s.get('content', '')
            if content:
                print(f"=== Step {idx} ({s['source']}/{s['type']}) ===")
                # encode safely for console
                clean = content.encode('ascii', errors='replace').decode('ascii')
                print(clean[:300])
                print()
            elif s.get('tool_calls'):
                for tc in s.get('tool_calls'):
                    print(f"=== Step {idx} TOOL CALL: {tc['name']} ===")
                    print(str(tc.get('args'))[:200])
