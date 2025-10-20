import os
import zipfile

BASE = r"C:\Users\gvvij\OneDrive\Desktop\MainCloudProject\mconnect"
OUT_ZIP = os.path.join(BASE, "deploy.zip")

INCLUDE_TOP = {"app.py", "requirements.txt", "templates", "static", "uploads"}  # uploads included
SKIP_DIRS = {".venv", "__pycache__"}
SKIP_FILES = {"database.db"}  # exclude local DB

def add_dir_entry(z, arcdir: str):
    if not arcdir.endswith("/"):
        arcdir += "/"
    # Add a directory entry so empty folders exist in ZIP
    z.writestr(arcdir, "")

def main():
    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        # Ensure top-level dirs get added even if empty
        for name in ("templates", "static", "uploads"):
            p = os.path.join(BASE, name)
            if os.path.isdir(p):
                add_dir_entry(z, name)

        for root, dirs, files in os.walk(BASE):
            rel_dir = os.path.relpath(root, BASE)
            parts = [] if rel_dir == "." else rel_dir.split(os.sep)

            # Skip unwanted dirs
            if any(part in SKIP_DIRS for part in parts):
                continue

            # Only include whitelisted top-level items
            if rel_dir != ".":
                top = parts[0]
                if top not in INCLUDE_TOP:
                    continue

            # Add directory entries to preserve structure
            if rel_dir != ".":
                arcdir = rel_dir.replace("\\", "/")
                add_dir_entry(z, arcdir)

            for f in files:
                if f in SKIP_FILES or f.endswith(".pyc"):
                    continue
                full = os.path.join(root, f)
                relpath = os.path.relpath(full, BASE)
                arcname = relpath.replace("\\", "/")  # force forward slashes
                z.write(full, arcname)

    print(f"Wrote {OUT_ZIP}")

if __name__ == "__main__":
    main()