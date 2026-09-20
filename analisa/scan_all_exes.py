from pathlib import Path

PR_PATTERNS = {
    "ProfileStage_ValidationOverride": (
        bytes.fromhex("0FB6800C010000C332C0C3"),
        bytes.fromhex("0FB6800C01000090B001C3")
    ),
    "PipelineRouting_StructuralRedirect": (
        bytes.fromhex("488B08C5F81001C5F811064C8976104C897618"),
        bytes.fromhex("488B08C5F81001C5F811064C8976004C897618")
    ),
    "PipelineRouting_FlagInitialization": (
        bytes.fromhex("66C783D000000000018B8424A8000000"),
        bytes.fromhex("66C783D000000001018B8424A8000000")
    ),
    "PipelineRouting_SecondaryBypass": (
        bytes.fromhex("4500C680D000000000498B75004881C690"),
        bytes.fromhex("4500C680D000000001498B75004881C690")
    ),
}

pr_dir = Path(r"D:\PR INSTALL\prsolved\pr")
for exe in sorted(pr_dir.glob("*.exe")):
    print(f"\nChecking {exe.name}...")
    with open(exe, "rb") as f:
        data = f.read()
    for name, (pat, repl) in PR_PATTERNS.items():
        orig_matches = []
        pos = 0
        while True:
            idx = data.find(pat, pos)
            if idx == -1:
                break
            orig_matches.append(idx)
            pos = idx + 1
        if orig_matches:
            print(f"  [{name}] MATCHED: {len(orig_matches)} {[hex(x) for x in orig_matches]}")
