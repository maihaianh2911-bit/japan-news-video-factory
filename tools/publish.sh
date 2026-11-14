#!/usr/bin/env bash
# Publish a folder to the 'renders' branch: the folder <dest_dir> is replaced as a whole by <source_dir>
# (nothing stale is left), and <dest_dir>/status.json records the stage, the run, the commit and the time.
#
#   tools/publish.sh <dest_dir> <source_dir> <stage> [<subfolder to keep>...]
#
# Subfolders named after the stage are kept as they are (render: "find", so the pictures found stay).
# OUTCOME (env, default "ok") is written in status.json, e.g. "partial" when some searches failed.
# PUBLISH_REMOTE (env) replaces the GitHub URL, for tests against a local repository.
# A file over 100 MB is refused by GitHub for good: it is reported at once (exit 2), not tried again.
# PUBLISH_MAX_BYTES (env) replaces that limit, for tests.
set -euo pipefail
DEST="${1:?dest_dir}"; SRC="${2:?source_dir}"; STAGE="${3:?stage}"; shift 3
KEEP=("$@")
[[ -d "$SRC" ]] || { echo "::error::nothing to publish: $SRC is not a folder"; exit 1; }
[[ "$DEST" != /* && "$DEST" != *..* && -n "${DEST//[\/.]/}" ]] || { echo "::error::bad dest_dir: $DEST"; exit 1; }
SRC=$(cd "$SRC" && pwd)
MAX_BYTES="${PUBLISH_MAX_BYTES:-100000000}"
BIG=$(find "$SRC" -type f -size +"${MAX_BYTES}c" -printf '%P (%s bytes)\n' | head -5)
if [[ -n "$BIG" ]]; then
  echo "::error::File quá nặng, GitHub không nhận file trên 100 MB (too large to publish): $BIG"
  exit 2
fi
PUSH_LOG=$(mktemp)
URL="${PUBLISH_REMOTE:-https://x-access-token:${GH_TOKEN}@github.com/${GITHUB_REPOSITORY}.git}"
RUN_URL="${GITHUB_SERVER_URL:-https://github.com}/${GITHUB_REPOSITORY:-local}/actions/runs/${GITHUB_RUN_ID:-0}"
COMMIT="${GITHUB_SHA:-$(git rev-parse HEAD)}"

attempt_publish() {
  local wt="$1" status
  # Start from the current tip of renders (or an empty branch if it does not exist yet).
  git ls-remote --exit-code --heads "$URL" renders >/dev/null && status=0 || status=$?
  if [[ $status == 0 ]]; then
    git fetch -q --depth 1 "$URL" "+refs/heads/renders:refs/remotes/origin/renders" || return 1
    git worktree add -q --detach "$wt" origin/renders || return 1
  elif [[ $status == 2 ]]; then
    git worktree add -q --detach "$wt" || return 1
    (cd "$wt" && git checkout -q --orphan "publish-tmp-$$" && { git rm -rfq . >/dev/null 2>&1 || true; } && git clean -fdqx) || return 1
  else
    return 1
  fi
  # Replace the folder, keeping only the listed subfolders. (Called from 'if': set -e is off here, so every
  # step checks its own status.)
  mkdir -p "$wt/$DEST" || return 1
  local entry name kept keep
  for entry in "$wt/$DEST"/* "$wt/$DEST"/.[!.]*; do
    [[ -e "$entry" ]] || continue
    name=$(basename "$entry"); keep=no
    for kept in "${KEEP[@]}"; do [[ "$name" == "$kept" ]] && keep=yes; done
    [[ $keep == yes ]] || rm -rf "$entry" || return 1
  done
  cp -r "$SRC"/. "$wt/$DEST/" || return 1
  STAGE="$STAGE" OUTCOME="${OUTCOME:-ok}" RUN_URL="$RUN_URL" COMMIT="$COMMIT" python3 - "$wt/$DEST/status.json" <<'PY' || return 1
import json, os, sys
from datetime import datetime, timezone
status = {"stage": os.environ["STAGE"], "outcome": os.environ["OUTCOME"],
          "run_id": os.environ.get("GITHUB_RUN_ID", ""), "run_url": os.environ["RUN_URL"],
          "commit": os.environ["COMMIT"], "published_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
open(sys.argv[1], "w", encoding="utf-8").write(json.dumps(status, indent=1) + "\n")
PY
  local who=(-c user.name=render-bot -c user.email=render-bot@users.noreply.github.com)
  git -C "$wt" "${who[@]}" add -A &&
    git -C "$wt" "${who[@]}" commit -q -m "publish $DEST ($STAGE, run ${GITHUB_RUN_ID:-local}, ${COMMIT:0:7})" || return 1
  git -C "$wt" push -q "$URL" HEAD:refs/heads/renders 2> "$PUSH_LOG" && status=0 || status=$?
  cat "$PUSH_LOG" >&2
  return $status
}

# A refusal that trying again cannot change (GitHub's file size limit, a rule on the branch).
permanent() {
  grep -qiE "GH001|exceeds GitHub's file size limit|pre-receive hook declined|protected branch" "$PUSH_LOG"
}

cleanup() {
  git worktree remove --force "$1" >/dev/null 2>&1 || rm -rf "$1"
  git worktree prune
  git branch -D "publish-tmp-$$" >/dev/null 2>&1 || true
}

for attempt in 1 2 3 4 5; do
  WT=$(mktemp -d); rmdir "$WT"
  if attempt_publish "$WT"; then
    cleanup "$WT"
    echo "published to renders/$DEST ($STAGE)"
    exit 0
  fi
  cleanup "$WT"
  if permanent; then
    echo "::error::GitHub từ chối nhận $DEST (refused for good, not trying again): xem dòng \"remote: error\" ở trên"
    exit 2
  fi
  : > "$PUSH_LOG"
  echo "publish attempt $attempt failed (renders moved or network error); starting again from the new tip"
  sleep $((attempt * 5))
done
echo "::error::could not publish $DEST to the renders branch after 5 attempts"
exit 1
