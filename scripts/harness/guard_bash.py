"""PreToolUse hook for Bash: stop shell writes from bypassing the Edit/Write gates.

Blocks a command when a write-shaped construct targets a gated path of THIS repo: a redirect
into it, a file command (cp/mv/rm/touch/tee/sed -i) naming it, or an inline script that
mentions it alongside a write call. Reads pass. Commands that never mention this repo pass.
"""

from __future__ import annotations

import json
import re
import sys

from progress import ROOT, UNLOCK

REPO = re.escape(ROOT.name)
GATED = rf"(?:{REPO}/)?(src/|tests/|PROGRESS\.md|ENDGOAL\.md|CLAUDE\.md)"
LOCKED = rf"(?:{REPO}/)?(scripts/harness|\.claude/|\.githooks|\.harness/)"
SEALED = re.compile(r"\.harness/")
ANY = f"(?:{GATED}|{LOCKED})"
REDIRECT = re.compile(rf"(?<![<>&])>{{1,2}}\s*['\"]?{ANY}")
FILE_CMD = re.compile(rf"\b(?:cp|mv|rm|touch|tee|sed\s+-i)\b[^|;&\n]*{ANY}")
SCRIPT_WRITE = re.compile(r"write_text|open\([^)]*['\"][wa]|\bshutil\b|os\.remove|\bunlink\b")
MENTIONS_LOCKED = re.compile(LOCKED)
MENTIONS_GATED = re.compile(GATED)


def decide(command: str) -> str | None:
    if ROOT.name not in command and "src/" not in command and "tests/" not in command:
        return None
    hit = REDIRECT.search(command) or FILE_CMD.search(command)
    script_hit = SCRIPT_WRITE.search(command) and (
        MENTIONS_GATED.search(command) or MENTIONS_LOCKED.search(command))
    if not (hit or script_hit):
        return None
    target = hit.group(0) if hit else command
    if SEALED.search(target):
        return "Harness lock: .harness/ is written only by the hooks or by Nikhil, never here."
    if MENTIONS_LOCKED.search(target) and not UNLOCK.exists():
        return ("Harness lock: shell writes to the harness are blocked until Nikhil creates "
                ".harness/unlock outside this session.")
    if MENTIONS_GATED.search(target):
        return ("Bash write to a gated path. Use the Edit/Write tools for src/, tests/, "
                "PROGRESS.md, ENDGOAL.md, CLAUDE.md so the loop and TDD gates apply.")
    return None


def main() -> None:
    payload = json.load(sys.stdin)
    cmd = payload.get("tool_input", {}).get("command", "")
    msg = decide(cmd)
    if msg:
        print(msg, file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
