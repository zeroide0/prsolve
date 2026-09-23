import urllib.request
import json
import subprocess

proc = subprocess.run(["git", "credential", "fill"], input="protocol=https\nhost=github.com\n", capture_output=True, text=True)
token = [l.split("=",1)[1].strip() for l in proc.stdout.splitlines() if l.startswith("password=")][0]

headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "User-Agent": "Python-Git"}

for repo in ["zeroide0/adobeprwrapper", "zeroide0/aepatch", "bearlikelion/resolve-patch"]:
    req = urllib.request.Request(f"https://api.github.com/repos/{repo}/pulls?state=all", headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            print(f"--- PRs for {repo} ({len(data)}) ---")
            for pr in data:
                print(f"  #{pr['number']} ({pr['state']}): {pr['title']} by {pr['user']['login']}")
                print(f"    Body: {pr['body']}")
    except Exception as e:
        print(f"Error {repo}: {e}")
