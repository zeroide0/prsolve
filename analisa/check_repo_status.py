import urllib.request
import json
import subprocess

proc = subprocess.run(['git', 'credential', 'fill'], input='protocol=https\nhost=github.com\n', capture_output=True, text=True)
token = [l.split('=',1)[1].strip() for l in proc.stdout.splitlines() if l.startswith('password=')][0]
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json', 'User-Agent': 'Python'}

def get_json(url):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

issues = get_json('https://api.github.com/repos/zeroide0/prsolve/issues?state=all')
print(f"Total Issues (including PRs): {len(issues)}")
for i in issues:
    print(f"Issue/PR #{i['number']}: {i['title']} [{i['state']}] comments={i['comments']}")

pulls = get_json('https://api.github.com/repos/zeroide0/prsolve/pulls?state=all')
print(f"Total PRs: {len(pulls)}")
for p in pulls:
    print(f"PR #{p['number']}: {p['title']} [{p['state']}]")

try:
    notifs = get_json('https://api.github.com/notifications')
    if notifs is not None:
        print(f"Total Unread Notifications: {len(notifs)}")
        for n in notifs:
            print(f"[{n['reason']}] {n['subject']['title']} ({n['subject']['type']})")
except Exception as e:
    print("Notification check failed:", e)

