import urllib.request
import json
import subprocess

proc = subprocess.run(['git', 'credential', 'fill'], input='protocol=https\nhost=github.com\n', capture_output=True, text=True)
token = [l.split('=',1)[1].strip() for l in proc.stdout.splitlines() if l.startswith('password=')][0]
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json', 'User-Agent': 'Python'}

def check_repo_issues(repo_name):
    req = urllib.request.Request(f'https://api.github.com/repos/{repo_name}/issues?state=all', headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            issues = json.loads(resp.read().decode())
        print(f"=== Issues on {repo_name}: {len(issues)} ===")
        for i in issues:
            print(f"Issue #{i['number']}: {i['title']} ({i['state']}) by {i['user']['login']}")
            print(f"URL: {i['html_url']}")
            print(f"Body:\n{i['body']}\n{'-'*50}")
    except Exception as e:
        print(f"Error {repo_name}: {e}")

check_repo_issues('zeroide0/prsolve')
