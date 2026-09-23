import urllib.request
import json
import subprocess

proc = subprocess.run(['git', 'credential', 'fill'], input='protocol=https\nhost=github.com\n', capture_output=True, text=True)
token = [l.split('=',1)[1].strip() for l in proc.stdout.splitlines() if l.startswith('password=')][0]
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json', 'User-Agent': 'Python'}

page = 1
all_repos = []
while True:
    req = urllib.request.Request(f'https://api.github.com/user/repos?per_page=100&page={page}', headers=headers)
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        if not data:
            break
        all_repos.extend(data)
        page += 1

print(f"Total repos for zeroide0: {len(all_repos)}")
found_prs = []
for r in all_repos:
    full_name = r['full_name']
    req_pr = urllib.request.Request(f'https://api.github.com/repos/{full_name}/pulls?state=all', headers=headers)
    try:
        with urllib.request.urlopen(req_pr) as resp_pr:
            prs = json.loads(resp_pr.read().decode())
            if prs:
                found_prs.append((full_name, prs))
    except Exception as e:
        print(f"Error {full_name}: {e}")

print(f"Repos with PRs: {len(found_prs)}")
for name, prs in found_prs:
    print(f"\n=== {name} ===")
    for pr in prs:
        print(f"  PR #{pr['number']}: {pr['title']} ({pr['state']}) by {pr['user']['login']}")
        print(f"    URL: {pr['html_url']}")
        print(f"    Body: {pr.get('body')}")
