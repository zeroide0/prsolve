import urllib.request
import json
import subprocess

proc = subprocess.run(["git", "credential", "fill"], input="protocol=https\nhost=github.com\n", capture_output=True, text=True)
token = [l.split("=",1)[1].strip() for l in proc.stdout.splitlines() if l.startswith("password=")][0]

headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "User-Agent": "Python-Git"}

req = urllib.request.Request("https://api.github.com/user/repos?type=all&per_page=100", headers=headers)
with urllib.request.urlopen(req) as resp:
    repos = json.loads(resp.read().decode())

print(f"Total repos: {len(repos)}")
for r in repos:
    r_name = r['full_name']
    # check issues
    req_i = urllib.request.Request(f"https://api.github.com/repos/{r_name}/issues?state=all", headers=headers)
    try:
        with urllib.request.urlopen(req_i) as resp_i:
            issues = json.loads(resp_i.read().decode())
            if issues:
                print(f"=== {r_name} has {len(issues)} issues/PRs ===")
                for item in issues:
                    is_pr = 'pull_request' in item
                    kind = "PR" if is_pr else "Issue"
                    print(f"  [{kind} #{item['number']}] {item['title']} ({item['state']}) by {item['user']['login']}")
                    print(f"    URL: {item['html_url']}")
                    print(f"    Body:\n{item['body']}\n")
    except Exception as e:
        pass
