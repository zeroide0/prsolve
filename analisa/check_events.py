import urllib.request
import json
import subprocess

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

# Check events (received events or user events)
print("--- User Events ---")
events = get_json("https://api.github.com/users/zeroide0/events")
if events:
    for ev in events[:10]:
        print(f"[{ev['type']}] on {ev['repo']['name']} at {ev['created_at']}")
        if ev['type'] in ('PullRequestEvent', 'PullRequestReviewEvent', 'IssuesEvent', 'IssueCommentEvent'):
            payload = ev.get('payload', {})
            print(f"  Payload: {payload.get('action')}")
            if 'pull_request' in payload:
                print(f"  PR Title: {payload['pull_request']['title']}")
                print(f"  PR URL: {payload['pull_request']['html_url']}")
                print(f"  PR Body: {payload['pull_request']['body']}")
            if 'issue' in payload:
                print(f"  Issue Title: {payload['issue']['title']}")
                print(f"  Issue Body: {payload['issue']['body']}")

# Search issues/PRs involving zeroide0
print("\n--- Search Involves zeroide0 ---")
search_res = get_json("https://api.github.com/search/issues?q=involves:zeroide0+is:pr")
if search_res and 'items' in search_res:
    for item in search_res['items']:
        print(f"PR #{item['number']}: {item['title']} on {item['repository_url']} ({item['state']})")
        print(f"  URL: {item['html_url']}")
        print(f"  Body: {item['body']}")

# Search issues involving zeroide0
search_issues = get_json("https://api.github.com/search/issues?q=involves:zeroide0+is:issue")
if search_issues and 'items' in search_issues:
    for item in search_issues['items']:
        print(f"Issue #{item['number']}: {item['title']} on {item['repository_url']} ({item['state']})")
        print(f"  URL: {item['html_url']}")
        print(f"  Body: {item['body']}")
