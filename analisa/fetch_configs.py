import urllib.request
import os

urls = {
    "config_v421.ini": "https://raw.githubusercontent.com/TheMythologist/GenP/main/v4.2.1/GenP/config.ini",
    "config_v420.ini": "https://raw.githubusercontent.com/TheMythologist/GenP/main/v4.2.0/GenP/config.ini",
    "config_v372.ini": "https://raw.githubusercontent.com/TheMythologist/GenP/main/v3.7.2/GenP/config.ini",
    "config_v404.ini": "https://raw.githubusercontent.com/TheMythologist/GenP/main/v4.0.4/GenP/config.ini",
}

for name, url in urls.items():
    dest = os.path.join(r"D:\PR INSTALL\prsolved\analisa", name)
    try:
        urllib.request.urlretrieve(url, dest)
        size = os.path.getsize(dest)
        print(f"Downloaded {name}: {size} bytes")
    except Exception as e:
        print(f"Failed {name}: {e}")
