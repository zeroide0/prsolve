import urllib.request
import subprocess

proc = subprocess.run(['git', 'credential', 'fill'], input='protocol=https\nhost=github.com\n', capture_output=True, text=True)
token = [l.split('=',1)[1].strip() for l in proc.stdout.splitlines() if l.startswith('password=')][0]
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json', 'User-Agent': 'Python'}

req = urllib.request.Request('https://api.github.com/user', headers=headers)
with urllib.request.urlopen(req) as resp:
    print("OAuth Scopes:", resp.headers.get('X-OAuth-Scopes'))
    print("User:", resp.read().decode()[:200])
