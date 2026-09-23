import urllib.request
import json
import subprocess

proc = subprocess.run(['git', 'credential', 'fill'], input='protocol=https\nhost=github.com\n', capture_output=True, text=True)
token = [l.split('=',1)[1].strip() for l in proc.stdout.splitlines() if l.startswith('password=')][0]
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json', 'User-Agent': 'Python'}

# Check bearlikelion/resolve-patch pull requests & issues
req = urllib.request.Request('https://api.github.com/repos/bearlikelion/resolve-patch/pulls?state=all', headers=headers)
with urllib.request.urlopen(req) as resp:
    prs = json.loads(resp.read().decode())
print(f"bearlikelion/resolve-patch PRs: {len(prs)}")
for p in prs[:5]:
    print(f"PR #{p['number']}: {p['title']} ({p['state']}) by {p['user']['login']}")
    print(f"  URL: {p['html_url']}")
    print(f"  Body: {p.get('body')}")

req2 = urllib.request.Request('https://api.github.com/repos/bearlikelion/resolve-patch/issues?state=all', headers=headers)
with urllib.request.urlopen(req2) as resp:
    issues = json.loads(resp.read().decode())
print(f"\nbearlikelion/resolve-patch Issues: {len(issues)}")
for i in issues[:5]:
    print(f"Issue #{i['number']}: {i['title']} ({i['state']}) by {i['user']['login']}")
    print(f"  URL: {i['html_url']}")
    print(f"  Body: {i.get('body')}")
