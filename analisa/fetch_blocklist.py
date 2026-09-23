import urllib.request

url = "https://raw.githubusercontent.com/ignaciocastro/a-dove-is-dumb/refs/heads/main/list.txt"
headers = {'User-Agent': 'Mozilla/5.0'}
req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req) as resp, open(r"D:\PR INSTALL\prsolved\analisa\adobe_blocklist.txt", "wb") as f:
        f.write(resp.read())
    print("Downloaded adobe_blocklist.txt successfully")
except Exception as e:
    print("Error:", e)
