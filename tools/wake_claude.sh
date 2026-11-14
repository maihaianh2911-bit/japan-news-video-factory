#!/usr/bin/env bash
# Start the Claude Code task right away (its API trigger). This is the only way Claude starts on its own: there is
# no hourly run. Needs repo secrets CLAUDE_TASK_URL (the task's "Fire URL") and CLAUDE_TASK_TOKEN. Never fails the
# workflow: without them, or when Claude is out of usage, the issue waits until the owner presses "Gọi Claude ngay"
# or works in a chat.
#
#   Usage: tools/wake_claude.sh "<why>" [<issue number>]
#
# With an issue number (and GH_TOKEN + GH_REPO in the environment):
# - an issue that carries a fresh `jnews-busy` (added less than 2 hours ago) is being worked on by a Claude in a
#   chat: Claude is not called and nothing is written on the issue;
# - a call that fails (after 3 tries) or that cannot be made (no secrets) is reported on the issue, so the owner
#   sees it without opening the run log. WAKE_COMMENT=no leaves that comment to the caller.
# Step outputs (GITHUB_OUTPUT): wake = ok | busy | nosecret | failed, note = the text for the issue when not called.
# The secrets are never printed.
set -u
ISSUE="${2:-}"
case "$ISSUE" in ''|*[!0-9]*) ISSUE= ;; esac
REPO="${GH_REPO:-${GITHUB_REPOSITORY:-}}"
WAKE_LINK="${GITHUB_SERVER_URL:-https://github.com}/$REPO/actions/workflows/wake.yml"

finish() {   # finish <result> [<note for the issue>]
  if [ -n "${GITHUB_OUTPUT:-}" ]; then
    echo "wake=$1" >> "$GITHUB_OUTPUT"
    [ -z "${2:-}" ] || echo "note=$2" >> "$GITHUB_OUTPUT"
  fi
  if [ -n "${2:-}" ] && [ -n "$ISSUE" ] && [ -n "${GH_TOKEN:-}" ] && [ -n "$REPO" ] && [ "${WAKE_COMMENT:-yes}" != no ]; then
    GH_REPO="$REPO" gh issue comment "$ISSUE" --body "$2" < /dev/null \
      || echo "::warning::wake: không ghi được bình luận lên phiếu #$ISSUE"
  fi
  exit 0
}

busy_fresh() {
  [ -n "$ISSUE" ] && [ -n "${GH_TOKEN:-}" ] && [ -n "$REPO" ] || return 1
  gh api "repos/$REPO/issues/$ISSUE" --jq '.labels[].name' 2>/dev/null | grep -qx 'jnews-busy' || return 1
  local since
  since=$(gh api "repos/$REPO/issues/$ISSUE/events?per_page=100" --paginate \
    --jq '.[] | select(.event == "labeled" and .label.name == "jnews-busy") | .created_at' 2>/dev/null | tail -n 1)
  [ -n "$since" ] || return 1
  python3 -c 'import sys
from datetime import datetime, timedelta, timezone
added = datetime.fromisoformat(sys.argv[1].replace("Z", "+00:00"))
sys.exit(0 if datetime.now(timezone.utc) - added < timedelta(hours=2) else 1)' "$since" 2>/dev/null
}

if busy_fresh; then
  echo "wake: phiếu #$ISSUE đang có nhãn jnews-busy (Claude đang làm trong chat): không gọi Claude"
  finish busy
fi

[ -n "${CLAUDE_TASK_URL:-}" ] && [ -n "${CLAUDE_TASK_TOKEN:-}" ] || {
  echo "::warning::Chưa cài CLAUDE_TASK_URL/CLAUDE_TASK_TOKEN: chưa gọi được Claude. Phiếu chờ đến khi thêm hai secret này rồi bấm Gọi Claude ngay, hoặc làm trong chat."
  if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
    printf '\n### Chưa gọi được Claude ngay\nThêm secrets `CLAUDE_TASK_URL` và `CLAUDE_TASK_TOKEN` (API trigger của tác vụ Claude cho repo này) để Claude bắt đầu ngay khi có việc. Không có lượt chạy mỗi giờ: hiện phiếu chờ đến khi bấm **Gọi Claude ngay** hoặc làm trong chat.\n' >> "$GITHUB_STEP_SUMMARY"
  fi
  finish nosecret "🤖 Chưa gọi được Claude: repo này chưa cài hai khóa CLAUDE_TASK_URL và CLAUDE_TASK_TOKEN. Phiếu này đang chờ. Hãy mở một chat với Claude và nhờ làm tiếp phiếu này. (Khi đã cài hai khóa thì bấm \"Gọi Claude ngay\" ở đây: $WAKE_LINK)"
}

WHY=$(printf '%s' "${1:-}" | python3 -c 'import json,sys;print(json.dumps({"text":sys.stdin.read()[:300]}))')
OUT=$(mktemp 2>/dev/null || echo "/tmp/wake-$$.json")
ERR=
for attempt in 1 2 3; do
  : > "$OUT"
  CODE=$(curl -s -o "$OUT" -w '%{http_code}' --max-time 30 -X POST "$CLAUDE_TASK_URL" \
    -H "Authorization: Bearer $CLAUDE_TASK_TOKEN" \
    -H "anthropic-beta: experimental-cc-routine-2026-04-01" -H "anthropic-version: 2023-06-01" \
    -H "Content-Type: application/json" -d "$WHY")
  RC=$?
  case "$CODE" in
    2*)
      echo "wake: Claude đã được gọi ($(python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('claude_code_session_url',''))" "$OUT" 2>/dev/null))"
      rm -f "$OUT"
      finish ok ;;
  esac
  if [ "$RC" -ne 0 ] || [ -z "$CODE" ] || [ "$CODE" = 000 ]; then ERR="không kết nối được, mã curl $RC"; else ERR="HTTP $CODE"; fi
  echo "wake: lần $attempt không được ($ERR)"
  head -c 300 "$OUT" 2>/dev/null; echo
  # a wrong address or token (4xx, except "too many requests") will not get better by trying again
  case "$CODE" in 4??) [ "$CODE" = 429 ] || break ;; esac
  [ "$attempt" = 3 ] || sleep $((attempt * 10))
done
rm -f "$OUT"
echo "::warning::wake: gọi Claude không được ($ERR) — bấm Gọi Claude ngay sau, hoặc làm trong chat"
if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
  printf '\n### Chưa gọi được Claude (%s)\nBấm **Gọi Claude ngay** trong Actions (khi Claude còn hạn mức), hoặc làm trong chat.\n' "$ERR" >> "$GITHUB_STEP_SUMMARY"
fi
finish failed "🤖 Chưa gọi được Claude ($ERR). Phiếu này đang chờ. Khi Claude còn hạn mức, bấm \"Gọi Claude ngay\" (nút Run workflow) ở đây: $WAKE_LINK — hoặc mở một chat với Claude và nhờ làm tiếp phiếu này."
