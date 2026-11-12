#!/usr/bin/env bash
# Copy files into a folder of the 'renders' branch and push. Usage: tools/publish.sh <dest_dir> <source_dir>
set -euo pipefail
DEST="$1"; SRC="$2"
URL="https://x-access-token:${GH_TOKEN}@github.com/${GITHUB_REPOSITORY}.git"
WT=$(mktemp -d)
if git fetch -q --depth 1 "$URL" "+refs/heads/renders:refs/remotes/origin/renders"; then
  git worktree add -q "$WT" origin/renders
else   # the renders branch does not exist yet: start it empty
  git worktree add -q --detach "$WT"
  (cd "$WT" && git checkout -q --orphan renders && { git rm -rf -q . || true; } && git clean -fdq)
fi
mkdir -p "$WT/$DEST"; cp -r "$SRC"/. "$WT/$DEST/"
cd "$WT"; git config user.name render-bot; git config user.email render-bot@users.noreply.github.com
git add -A; git commit -q -m "publish $DEST ($GITHUB_RUN_ID)" || true
for i in 1 2 3; do
  git push -q "$URL" HEAD:renders && { echo "published to renders/$DEST"; exit 0; }
  git fetch -q --depth 1 "$URL" "+refs/heads/renders:refs/remotes/origin/renders" && git rebase -q origin/renders || true
  sleep $((i * 5))
done
echo "::error::could not push to renders"; exit 1
