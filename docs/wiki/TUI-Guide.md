# TUI Guide

Launch with:

```bash
habit tui
```

## Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Habit Tracker                              12:34:56        │
├──────────────────┬──────────────────────────────────────────┤
│  Habits          │  Range: year  (1=year  2=quarter  3=month)│
│                  │                                           │
│ > 🏃 Morning Run │  Jan Feb Mar Apr May Jun                  │
│   📚 Read 30min  │      ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■            │
│   🧘 Meditate    │  Mon ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■            │
│                  │      ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■            │
│                  │  Wed ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■            │
│                  │      ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■            │
│                  │  Fri ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■            │
│                  │      ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■            │
│                  ├──────────────────────────────────────────┤
│                  │  🏃 Morning Run                           │
│                  │                                           │
│                  │  Today          ✓ Done                    │
│                  │  Current streak  5 days                   │
│                  │  Longest streak  12 days                  │
│                  │  Completion      68.2%                    │
│                  │  Total logged    156 days                  │
│                  │  Daily target    3                         │
│                  │                                           │
│                  │  Keys: d=done u=undo a=add x=delete ...   │
├──────────────────┴──────────────────────────────────────────┤
│  q Quit  d Done today  u Undo today  a Add habit  ...       │
└─────────────────────────────────────────────────────────────┘
```

## Keybindings

| Key | Action |
|-----|--------|
| `d` | Mark the selected habit done for today |
| `u` | Undo today's entry for the selected habit |
| `a` | Show the add-habit input bar; type a name and press Enter |
| `x` | Delete the selected habit (and all its entries) |
| `1` | Switch to **year** range |
| `2` | Switch to **quarter** range |
| `3` | Switch to **month** range |
| `j` or `↓` | Move selection down |
| `k` or `↑` | Move selection up |
| `Esc` | Cancel the add-habit input |
| `q` | Quit |

## Adding a habit

Press `a` — an input bar appears at the bottom. Type the habit name and press Enter. The habit is created with no target or emoji; you can set those via `habit add` from the CLI before launching the TUI, or edit the database directly.

## Notifications

After marking done, undoing, or creating a habit, a toast notification appears in the top-right corner for a few seconds.
