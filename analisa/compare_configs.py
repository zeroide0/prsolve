import os

configs = [
    "config_v372.ini",
    "config_v404.ini",
    "config_v420.ini",
    "config_v421.ini"
]

for cfg in configs:
    p = os.path.join(r"D:\PR INSTALL\prsolved\analisa", cfg)
    if not os.path.exists(p):
        continue
    print(f"\n=================== {cfg} ===================")
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    for l in lines:
        if "premiere" in l.lower() and "=" in l:
            print("  ", l.strip())
