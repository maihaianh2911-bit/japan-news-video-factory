"""Print the issue number of a story file ("issue": N), or nothing. Usage: python tools/story_issue.py stories/<name>.json
A file that is not valid JSON is still searched for its "issue" field, so the failure can be reported on its issue."""
import json
import re
import sys

try:
    raw = open(sys.argv[1], encoding="utf-8", errors="replace").read()
except OSError:
    raw = ""
try:
    number = json.loads(raw).get("issue")
except (ValueError, AttributeError):
    found = re.findall(r'"issue"\s*:\s*(\d+)\s*[,}\n]', raw)
    number = int(found[0]) if len(set(found)) == 1 else None
print(number if isinstance(number, int) and not isinstance(number, bool) and number > 0 else "")
