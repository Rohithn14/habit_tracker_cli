# Shell Integration

habit-tracker can print a compact summary automatically every time you open an interactive terminal.

## Installing the hook

```bash
habit shell-install
```

This appends a marked block to `~/.zshrc`:

```zsh
# >>> habit-tracker >>>
if [[ -o interactive ]] && command -v habit >/dev/null 2>&1; then
  habit summary 2>/dev/null
fi
# <<< habit-tracker <<<
```

Open a new terminal — you should see something like:

```
🏃 Morning Run  ▁▁▆▆█▆▁▁  🔥 5d  ✓
📚 Read 30min   ▁▃▁▆▃▆█▁  🔥 2d  ·
🧘 Meditate     ▁▁▁▃▆▆▆█  🔥 4d  ✓
```

## Removing the hook

```bash
habit shell-install --remove
```

Strips only the marked block — leaves the rest of `~/.zshrc` untouched.

## Checking hook status

```bash
grep -c "habit-tracker" ~/.zshrc
```

Returns `2` (the two markers) if installed, `0` if not.

## Safety guarantees

- Only runs in interactive shells (`[[ -o interactive ]]`).
- Only runs when `habit` is on `PATH` (`command -v habit`).
- All output from `habit summary` is discarded to `/dev/null` on error (`2>/dev/null`).
- `habit summary` itself wraps all logic in `try/except: pass` — it can never raise or print a traceback.
- Cold start time is ~200ms on a typical machine (Rich + SQLite read; Textual is **not** imported).

## Performance

If startup feels slow, check:

```bash
time habit summary
```

Under 500ms is normal. If it's slower, the database may have grown large — `habit export` + delete + `habit import` will compact it.
