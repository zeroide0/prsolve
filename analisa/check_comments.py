import urllib.request
import json
import subprocess

proc = subprocess.run(['git', 'credential', 'fill'], input='protocol=https\nhost=github.com\n', capture_output=True, text=True)
token = [l.split('=',1)[1].strip() for l in proc.stdout.splitlines() if l.startswith('password=')][0]
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json', 'User-Agent': 'Python'}

for issue_num in [1, 2, 3]:
    req = urllib.request.Request(f'https://api.github.com/repos/zeroide0/prsolve/issues/{issue_num}/comments', headers=headers)
    with urllib.request.urlopen(req) as resp:
        comments = json.loads(resp.read().decode())
    print(f'=== Comments on Issue #{issue_num}: {len(comments)} ===')
    for c in comments:
        print(f"[{c['user']['login']}] {c['created_at']}: {c['body']}")
