"""Shell startup hook management for ~/.zshrc."""
from __future__ import annotations

from pathlib import Path

_MARKER_START = "# >>> habit-tracker >>>"
_MARKER_END = "# <<< habit-tracker <<<"

_SNIPPET = """\
# >>> habit-tracker >>>
if [[ -o interactive ]] && command -v habit >/dev/null 2>&1; then
  habit summary 2>/dev/null
fi
# <<< habit-tracker <<<"""


def _rc_path() -> Path:
    return Path.home() / ".zshrc"


def is_installed(rc_path: Path | None = None) -> bool:
    path = rc_path or _rc_path()
    if not path.exists():
        return False
    return _MARKER_START in path.read_text()


def install(rc_path: Path | None = None) -> bool:
    """Append the hook block to the shell rc file. Returns True if added, False if already present."""
    path = rc_path or _rc_path()
    if is_installed(path):
        return False
    with open(path, "a") as f:
        f.write(f"\n{_SNIPPET}\n")
    return True


def remove(rc_path: Path | None = None) -> bool:
    """Remove the hook block from the shell rc file. Returns True if removed."""
    path = rc_path or _rc_path()
    if not path.exists() or not is_installed(path):
        return False

    lines = path.read_text().splitlines(keepends=True)
    out: list[str] = []
    inside = False
    for line in lines:
        stripped = line.rstrip("\n")
        if stripped == _MARKER_START:
            inside = True
            continue
        if stripped == _MARKER_END:
            inside = False
            continue
        if not inside:
            out.append(line)

    # Remove trailing blank line added by install
    while out and out[-1].strip() == "":
        out.pop()
    out.append("\n")

    path.write_text("".join(out))
    return True
