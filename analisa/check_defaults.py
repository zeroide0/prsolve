for cfg in ["config_v372.ini", "config_v404.ini", "config_v420.ini", "config_v421.ini"]:
    p = r"D:\PR INSTALL\prsolved\analisa\\" + cfg
    with open(p, "r") as f:
        content = f.read()
    print(f"=== {cfg} ===")
    for line in content.splitlines():
        if "defaultpatterns" in line.lower() or "custompatterns" in line.lower():
            print(line)
        if line.startswith("Values="):
            print(" ", line)
