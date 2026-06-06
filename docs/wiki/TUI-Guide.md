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

## Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Habit Tracker                              12:34:56        │
├──────────────────┬──────────────────────────────────────────┤
│  ✦ Habits        │  🏃 Morning Run  ●  3/3 today            │
│                  │──────────────────────────────────────────│
│ > 🏃 Morning Run │  Activity (heatmap)                      │
│   🔥 3d · 3/3   │  Jan Feb Mar Apr ...                     │
│   📚 Read 30min  │      ■ ■ ■ ■ ■• ■ ...  (• = note)       │
│   🧘 Meditate    │  Mon ■ ■ ■ ■ ■ ■ ...                    │
│                  │      [day detail on click]               │
│                  │──────────────────────────────────────────│
│                  │  Trend             │  By Day             │
│                  │  7-day rolling 85% │  Mon ████████  82%  │
│                  │  ▁▂▄▅▆▇█▇█▆▇█     │  Tue ██████░░  60%  │
│                  │                    │  ...                │
│                  │──────────────────────────────────────────│
│                  │  📅 TODAY │ 🔥 3d │ 🏆 12d │ 📊 80%     │
├──────────────────┴──────────────────────────────────────────┤
│  q Quit  d Done  c Count  u Undo  n Note  a Add  x Delete   │
└─────────────────────────────────────────────────────────────┘
```

## Keybindings

| Key | Action |
|-----|--------|
| `d` | Mark the selected habit done for today |
| `c` | Log a custom count for today |
| `u` | Undo today's entry for the selected habit |
| `n` | Add or edit a note for today's entry |
| `/` | Open the sidebar search filter |
| `a` | Show the add-habit input bar; type a name and press Enter |
| `x` | Delete the selected habit (and all its entries) |
| `1` | Switch to **year** range |
| `2` | Switch to **quarter** range |
| `3` | Switch to **month** range |
| `j` or `↓` | Move selection down |
| `k` or `↑` | Move selection up |
| `Ctrl+P` | Open the command palette |
| `Esc` | Cancel any active input / clear search |
| `q` | Quit |

## Adding a habit

Press `a` — an input bar appears at the bottom. Type the habit name and press Enter. The habit is created with no target or emoji; you can set those via `habit add` from the CLI before launching the TUI.

## Adding a note

Press `n` — an input bar appears at the bottom pre-filled with any existing note for today. Type your note and press Enter to save (or Esc to cancel). Notes are stored per day and do not affect streak or completion calculations.

## Clicking a heatmap cell

Click any colored cell in the **Activity** section to see that day's detail panel below the heatmap: the date, logged count (with % of target if set), and note if one exists. Clicking another cell updates the panel; switching habits clears it.

Cells with notes show a violet `•` marker (`■•`) — the legend at the bottom of the heatmap explains the indicator.

## Searching / filtering habits

Press `/` — a search bar appears at the bottom. Typing immediately filters the sidebar to matching habits. Press `Esc` to clear the filter and restore the full list.

The search is also available from the command palette (`Ctrl+P → Search habits…`).

## Analytics panels

Below the heatmap, two cards are always visible:

- **Trend** — a Unicode sparkline of the 7-day rolling completion rate over the last 90 days. The current rate is shown in green (≥70%), amber (≥40%), or dim (<40%).
- **By Day** — a horizontal bar chart showing your completion rate for each weekday (Mon–Sun) across all history. Useful for spotting which days you tend to skip.

On narrow terminals (< 100 columns) both panels are hidden automatically and the sidebar collapses to icon-only view.

The CLI command `habit show NAME` also prints the day-of-week breakdown below the stats panel.

## Notifications

After marking done, undoing, adding a note, or creating a habit, a toast notification appears in the top-right corner for a few seconds.
