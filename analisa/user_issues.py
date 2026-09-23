import urllib.request
import json
import subprocess

proc = subprocess.run(['git', 'credential', 'fill'], input='protocol=https\nhost=github.com\n', capture_output=True, text=True)
token = [l.split('=',1)[1].strip() for l in proc.stdout.splitlines() if l.startswith('password=')][0]
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json', 'User-Agent': 'Python'}

# /user/issues?filter=all&state=all lists all issues & PRs across all repositories owned or subscribed by the authenticated user
req = urllib.request.Request('https://api.github.com/user/issues?filter=all&state=all', headers=headers)
with urllib.request.urlopen(req) as resp:
    issues = json.loads(resp.read().decode())

print(f"Total issues/PRs from /user/issues: {len(issues)}")
for i in issues:
    is_pr = 'pull_request' in i
    tag = "PR" if is_pr else "Issue"
    print(f"[{tag} #{i['number']}] {i['title']} on {i['repository']['full_name']}")
    print(f"  URL: {i['html_url']}")
    print(f"  Body: {i.get('body')}")
    print()
