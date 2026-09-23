import urllib.request

urls = {
    "hosts": "https://raw.githubusercontent.com/TheMythologist/GenP/main/v4.2.1/GenP/resources/hosts",
    "UpdateHostsFile.ps1": "https://raw.githubusercontent.com/TheMythologist/GenP/main/v4.2.1/GenP/resources/UpdateHostsFile.ps1",
    "RemoveGudeLogs.ps1": "https://raw.githubusercontent.com/TheMythologist/GenP/main/v4.2.1/GenP/resources/RemoveGudeLogs.ps1",
}

headers = {'User-Agent': 'Mozilla/5.0'}
for name, url in urls.items():
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as resp, open(rf"D:\PR INSTALL\prsolved\analisa\{name}", "wb") as f:
            f.write(resp.read())
        print(f"Downloaded {name}")
    except Exception as e:
        print(f"Failed {name}: {e}")
