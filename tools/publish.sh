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
# PUBLISH_MODE=add (env): only add or replace the files of <source_dir> in an existing <dest_dir>; nothing else in
# it is removed and status.json is left as it is (used for the posting caption beside a finished video). Exit 3
# when <dest_dir> does not exist on renders yet (nothing to add to).
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
  if [[ "${PUBLISH_MODE:-}" == add ]]; then
    [[ -d "$wt/$DEST" ]] || return 3
    cp -r "$SRC"/. "$wt/$DEST/" || return 1
    git -C "$wt" add -A || return 1
    if git -C "$wt" diff --cached --quiet; then NOTHING=yes; return 0; fi
    git -C "$wt" -c user.name=render-bot -c user.email=render-bot@users.noreply.github.com \
      commit -q -m "publish $DEST ($STAGE, run ${GITHUB_RUN_ID:-local}, ${COMMIT:0:7})" || return 1
    git -C "$wt" push -q "$URL" HEAD:refs/heads/renders 2> "$PUSH_LOG" && status=0 || status=$?
    cat "$PUSH_LOG" >&2
    return $status
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

# A refusal that trying again cannot change (GitHub's file size limit, a rule on the branch). Only "remote: error"
# lines count: a file between 50 and 100 MB gets "remote: warning: GH001 …" and is accepted, and a push that lost
# the race against another job ("cannot lock ref", "fetch first") must be tried again.
permanent() {
  grep -qiE "remote: error:.*(GH001|exceeds GitHub's file size limit)|pre-receive hook declined|protected branch" "$PUSH_LOG"
}

cleanup() {
  git worktree remove --force "$1" >/dev/null 2>&1 || rm -rf "$1"
  git worktree prune
  git branch -D "publish-tmp-$$" >/dev/null 2>&1 || true
}

# Several jobs of one push may publish at the same time: up to 8 tries, with a random wait so they spread out.
for attempt in 1 2 3 4 5 6 7 8; do
  WT=$(mktemp -d); rmdir "$WT"
  NOTHING=no
  attempt_publish "$WT" && result=0 || result=$?
  cleanup "$WT"
  if [[ $result == 0 ]]; then
    [[ $NOTHING == yes ]] && echo "renders/$DEST already has these files: nothing to publish" || echo "published to renders/$DEST ($STAGE)"
    exit 0
  fi
  if [[ $result == 3 ]]; then
    echo "renders/$DEST does not exist yet: nothing to add to"
    exit 3
  fi
  if permanent; then
    echo "::error::GitHub từ chối nhận $DEST (refused for good, not trying again): xem dòng \"remote: error\" ở trên"
    exit 2
  fi
  : > "$PUSH_LOG"
  echo "publish attempt $attempt failed (renders moved or network error); starting again from the new tip"
  sleep $((attempt * 4 + RANDOM % 7))
done
echo "::error::could not publish $DEST to the renders branch after 8 attempts"
exit 1
