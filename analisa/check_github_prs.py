import urllib.request
import json
import subprocess

# Get token from git credential
proc = subprocess.run(
    ["git", "credential", "fill"],
    input="protocol=https\nhost=github.com\n",
    capture_output=True,
    text=True
)
token = None
for line in proc.stdout.splitlines():
    if line.startswith("password="):
        token = line.split("=", 1)[1].strip()

if not token:
    print("No token found")
    exit(1)

headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github+json",
    "User-Agent": "Python-Git-Script"
}

def get_json(url):
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"Error fetching {url}: {e.code} {e.reason}")
        return None

# Check notifications
print("--- Notifications ---")
notifs = get_json("https://api.github.com/notifications?all=true")
if notifs:
    for n in notifs[:5]:
        print(f"[{n.get('reason')}] {n.get('subject', {}).get('title')} ({n.get('subject', {}).get('url')})")
else:
    print("No notifications found or empty")

# Check pull requests on zeroide0/prsolve
print("\n--- Pull Requests on zeroide0/prsolve ---")
prs = get_json("https://api.github.com/repos/zeroide0/prsolve/pulls?state=all")
if prs:
    for pr in prs:
        print(f"PR #{pr['number']}: {pr['title']} by {pr['user']['login']} ({pr['state']})")
        print(f"  URL: {pr['html_url']}")
        print(f"  Body: {pr['body']}")
else:
    print("No PRs on zeroide0/prsolve")

# Also check other repos of zeroide0
print("\n--- Repos of zeroide0 ---")
repos = get_json("https://api.github.com/user/repos?sort=updated")
if repos:
    for r in repos[:10]:
        print(f"{r['full_name']} (private: {r['private']})")
        if r['full_name'] != 'zeroide0/prsolve':
            r_prs = get_json(f"https://api.github.com/repos/{r['full_name']}/pulls?state=all")
            if r_prs:
                for pr in r_prs:
                    print(f"  PR #{pr['number']}: {pr['title']} by {pr['user']['login']}")
