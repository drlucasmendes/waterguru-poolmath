#!/usr/bin/env bash
set -euo pipefail

read -rp "GitHub username: " GITHUB_USER
read -rp "Repository name [waterguru-poolmath]: " REPO_NAME
REPO_NAME="${REPO_NAME:-waterguru-poolmath}"

python3 - "$GITHUB_USER" "$REPO_NAME" <<'PY'
import json, pathlib, sys
user, repo = sys.argv[1], sys.argv[2]
manifest_path = pathlib.Path("custom_components/waterguru_poolmath/manifest.json")
manifest = json.loads(manifest_path.read_text())
manifest["documentation"] = f"https://github.com/{user}/{repo}"
manifest["issue_tracker"] = f"https://github.com/{user}/{repo}/issues"
manifest["codeowners"] = [f"@{user}"]
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
PY

echo
echo "Repository metadata updated for https://github.com/${GITHUB_USER}/${REPO_NAME}"
echo "Next:"
echo "  git init"
echo "  git add ."
echo '  git commit -m "Initial release"'
echo "  git branch -M main"
echo "  git remote add origin https://github.com/${GITHUB_USER}/${REPO_NAME}.git"
echo "  git push -u origin main"
