import urllib.request
import json
import subprocess

proc = subprocess.run(['git', 'credential', 'fill'], input='protocol=https\nhost=github.com\n', capture_output=True, text=True)
token = [l.split('=',1)[1].strip() for l in proc.stdout.splitlines() if l.startswith('password=')][0]
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json', 'User-Agent': 'Python'}

# Check forks of zeroide0/prsolve
req = urllib.request.Request('https://api.github.com/repos/zeroide0/prsolve/forks', headers=headers)
with urllib.request.urlopen(req) as resp:
    forks = json.loads(resp.read().decode())
print(f"Forks of zeroide0/prsolve: {len(forks)}")
for f in forks:
    print(f"  Fork: {f['full_name']} by {f['owner']['login']}")
