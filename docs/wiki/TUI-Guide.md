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
| `c` | Log a custom count for today |
| `u` | Undo today's entry for the selected habit |
| `n` | Add or edit a note for today's entry |
| `a` | Show the add-habit input bar; type a name and press Enter |
| `x` | Delete the selected habit (and all its entries) |
| `1` | Switch to **year** range |
| `2` | Switch to **quarter** range |
| `3` | Switch to **month** range |
| `j` or `↓` | Move selection down |
| `k` or `↑` | Move selection up |
| `Ctrl+P` | Open the command palette |
| `Esc` | Cancel any active input |
| `q` | Quit |

## Adding a habit

Press `a` — an input bar appears at the bottom. Type the habit name and press Enter. The habit is created with no target or emoji; you can set those via `habit add` from the CLI before launching the TUI.

## Adding a note

Press `n` — an input bar appears at the bottom pre-filled with any existing note for today. Type your note and press Enter to save (or Esc to cancel). Notes are stored per day and do not affect streak or completion calculations.

## Clicking a heatmap cell

Click any colored cell in the **Activity** section to see that day's detail panel below the heatmap: the date, logged count (with % of target if set), and note if one exists. Clicking another cell updates the panel; switching habits clears it.

Cells with notes show a violet `•` marker (`■•`) — the legend at the bottom of the heatmap explains the indicator.

## Notifications

After marking done, undoing, adding a note, or creating a habit, a toast notification appears in the top-right corner for a few seconds.
