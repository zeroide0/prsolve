import json

path = r'C:\Users\Acer\.gemini\antigravity-cli\brain\120edaaa-745a-4c0c-9fd8-f3834e71f89f\.system_generated\logs\transcript.jsonl'
with open(path, 'r', encoding='utf-8') as f:
    for line in f:
        s = json.loads(line)
        content = s.get('content', '')
        if any(w in content for w in ['PromptUpgradeHEVC', 'suppress_dialog_prompt', 'test_dialog_patch']):
            print(f"Step {s.get('step_index')}:")
            clean = content.encode('ascii', errors='replace').decode('ascii')
            print(clean[:400])
            print('='*50)
