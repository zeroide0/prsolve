import urllib.request

headers = {'User-Agent': 'Mozilla/5.0'}

img1_url = "https://github.com/user-attachments/assets/6f63c911-b522-4a2b-9854-966dc6bdb39f"
img2_url = "https://github.com/user-attachments/assets/d2f63202-ed1a-46da-a33e-b28210e4c490"

req1 = urllib.request.Request(img1_url, headers=headers)
with urllib.request.urlopen(req1) as resp, open(r"D:\PR INSTALL\prsolved\analisa\issue_img1.png", "wb") as f:
    f.write(resp.read())
print("Downloaded issue_img1.png")

req2 = urllib.request.Request(img2_url, headers=headers)
with urllib.request.urlopen(req2) as resp, open(r"D:\PR INSTALL\prsolved\analisa\issue_img2.png", "wb") as f:
    f.write(resp.read())
print("Downloaded issue_img2.png")
