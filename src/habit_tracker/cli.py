"""Habit tracker CLI — all Typer commands."""
from __future__ import annotations

import sys
from datetime import date
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.text import Text

app = typer.Typer(
    name="habit",
    help="Terminal habit tracker with GitHub-style heatmaps.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

console = Console()
err_console = Console(stderr=True)

RangeArg = typer.Option(
    "year", "--range", "-r",
    help="Time range: year | quarter | month | last:30d | last:6w | YYYY-MM-DD:YYYY-MM-DD",
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _require_habit(name: str):
    from habit_tracker.storage import get_habit
    h = get_habit(name)
    if h is None:
        err_console.print(f"[red]Habit '[bold]{name}[/bold]' not found.[/red]")
        raise typer.Exit(1)
    return h


def _parse_date(value: Optional[str]) -> date:
    if value is None:
        return date.today()
    try:
        return date.fromisoformat(value)
    except ValueError:
        err_console.print(f"[red]Invalid date '{value}'. Use YYYY-MM-DD.[/red]")
        raise typer.Exit(1)


# ── Lifecycle ─────────────────────────────────────────────────────────────────

@app.callback(invoke_without_command=True)
def _callback(ctx: typer.Context) -> None:
    from habit_tracker.storage import init_db
    init_db()
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


# ── Commands ──────────────────────────────────────────────────────────────────

@app.command()
def add(
    name: str = typer.Argument(..., help="Habit name"),
    emoji: str = typer.Option("", "--emoji", "-e", help="Emoji prefix"),
    color: str = typer.Option("green", "--color", "-c", help="Accent color name"),
    target: Optional[int] = typer.Option(None, "--target", "-t", help="Daily count target for intensity shading"),
    schedule: Optional[str] = typer.Option(None, "--schedule", "-s", help="Frequency: daily | weekly:N | dow:1,3,5 (1=Mon)"),
    category: Optional[str] = typer.Option(None, "--category", help="Group label for the habit"),
) -> None:
    """Create a new habit."""
    from habit_tracker.colors import is_valid_color, colors_hint
    from habit_tracker.schedule import is_valid_schedule
    from habit_tracker.storage import create_habit, get_habit
    if not is_valid_color(color):
        err_console.print(f"[red]Unknown color '{color}'. Choose one of: {colors_hint()}[/red]")
        raise typer.Exit(1)
    if not is_valid_schedule(schedule):
        err_console.print(f"[red]Invalid schedule '{schedule}'. Use daily | weekly:N | dow:1,3,5.[/red]")
        raise typer.Exit(1)
    if get_habit(name):
        err_console.print(f"[yellow]Habit '[bold]{name}[/bold]' already exists.[/yellow]")
        raise typer.Exit(1)
    h = create_habit(name, emoji=emoji, color=color, target=target, schedule=schedule, category=category)
    label = h.label
    console.print(f"[green]✓[/green] Created habit [bold]{label}[/bold]" + (f" (target: {target}/day)" if target else ""))


@app.command()
def edit(
    name: str = typer.Argument(..., help="Habit to edit (current name)"),
    new_name: Optional[str] = typer.Option(None, "--name", help="New name"),
    emoji: Optional[str] = typer.Option(None, "--emoji", "-e", help="New emoji prefix"),
    color: Optional[str] = typer.Option(None, "--color", "-c", help="New accent color"),
    target: Optional[int] = typer.Option(None, "--target", "-t", help="New daily target"),
    clear_target: bool = typer.Option(False, "--clear-target", help="Remove the target"),
    schedule: Optional[str] = typer.Option(None, "--schedule", "-s", help="Frequency: daily | weekly:N | dow:1,3,5"),
    category: Optional[str] = typer.Option(None, "--category", help="Group label"),
) -> None:
    """Update an existing habit's name, emoji, color, target, schedule, or category."""
    import sqlite3
    from habit_tracker.colors import is_valid_color, colors_hint
    from habit_tracker.schedule import is_valid_schedule
    from habit_tracker.storage import update_habit, get_habit, _UNSET
    h = _require_habit(name)

    if color is not None and not is_valid_color(color):
        err_console.print(f"[red]Unknown color '{color}'. Choose one of: {colors_hint()}[/red]")
        raise typer.Exit(1)
    if schedule is not None and not is_valid_schedule(schedule):
        err_console.print(f"[red]Invalid schedule '{schedule}'. Use daily | weekly:N | dow:1,3,5.[/red]")
        raise typer.Exit(1)
    if clear_target and target is not None:
        err_console.print("[red]Use either --target or --clear-target, not both.[/red]")
        raise typer.Exit(1)
    if new_name is not None and new_name != name and get_habit(new_name):
        err_console.print(f"[yellow]Habit '[bold]{new_name}[/bold]' already exists.[/yellow]")
        raise typer.Exit(1)

    # "daily" normalizes to NULL (the default); other schedule strings pass through.
    sched_arg = _UNSET if schedule is None else (None if schedule.strip().lower() == "daily" else schedule)
    cat_arg = _UNSET if category is None else category
    target_arg = None if clear_target else (target if target is not None else _UNSET)
    try:
        updated = update_habit(
            h.id, name=new_name, emoji=emoji, color=color,
            target=target_arg, schedule=sched_arg, category=cat_arg,
        )
    except sqlite3.IntegrityError:
        err_console.print(f"[yellow]Habit '[bold]{new_name}[/bold]' already exists.[/yellow]")
        raise typer.Exit(1)
    label = updated.label
    console.print(f"[green]✓[/green] Updated [bold]{label}[/bold]")


@app.command()
def done(
    name: str = typer.Argument(..., help="Habit name"),
    date_str: Optional[str] = typer.Option(None, "--date", "-d", help="Date (YYYY-MM-DD), defaults to today"),
    count: int = typer.Option(1, "--count", "-n", help="Count logged for this day"),
) -> None:
    """Mark a habit as done for a day."""
    from habit_tracker.storage import log_entry
    h = _require_habit(name)
    day = _parse_date(date_str)
    log_entry(h.id, day, count=count)
    label = h.label
    console.print(f"[green]✓[/green] [bold]{label}[/bold] logged for {day.isoformat()}" + (f" (×{count})" if count > 1 else ""))


@app.command()
def undo(
    name: str = typer.Argument(..., help="Habit name"),
    date_str: Optional[str] = typer.Option(None, "--date", "-d", help="Date (YYYY-MM-DD), defaults to today"),
    from_str: Optional[str] = typer.Option(None, "--from", help="Start of date range to remove (YYYY-MM-DD)"),
    to_str: Optional[str] = typer.Option(None, "--to", help="End of date range to remove (YYYY-MM-DD)"),
) -> None:
    """Remove logged entries for a day or a date range (--from / --to)."""
    from habit_tracker.storage import remove_entry, remove_entries_range
    h = _require_habit(name)
    label = h.label

    if from_str or to_str:
        since = _parse_date(from_str)
        until = _parse_date(to_str)
        if since > until:
            err_console.print("[red]--from must be on or before --to[/red]")
            raise typer.Exit(1)
        count = remove_entries_range(h.id, since, until)
        if count:
            console.print(f"[yellow]↩[/yellow] Removed [bold]{count}[/bold] entries for [bold]{label}[/bold] ({since} → {until})")
        else:
            err_console.print(f"[dim]No entries found for {label} in that range[/dim]")
            raise typer.Exit(1)
    else:
        day = _parse_date(date_str)
        removed = remove_entry(h.id, day)
        if removed:
            console.print(f"[yellow]↩[/yellow] Removed log for [bold]{label}[/bold] on {day.isoformat()}")
        else:
            err_console.print(f"[dim]No entry found for {label} on {day.isoformat()}[/dim]")
            raise typer.Exit(1)


@app.command()
def note(
    name: str = typer.Argument(..., help="Habit name"),
    text: str = typer.Argument(..., help="Note text to attach to today's entry"),
    date_str: Optional[str] = typer.Option(None, "--date", "-d", help="Date (YYYY-MM-DD), defaults to today"),
) -> None:
    """Attach a text note to a habit entry."""
    from habit_tracker.storage import set_entry_note
    h = _require_habit(name)
    day = _parse_date(date_str)
    set_entry_note(h.id, day, text)
    label = h.label
    console.print(f"[green]📝[/green] Note saved for [bold]{label}[/bold] on {day.isoformat()}")


@app.command(name="list")
def list_habits_cmd(
    all_: bool = typer.Option(False, "--all", "-a", help="Include archived habits"),
) -> None:
    """List all habits."""
    from habit_tracker.storage import list_habits, get_entries
    from habit_tracker.stats import build_stats
    habits = list_habits(include_archived=all_)
    if not habits:
        console.print("[dim]No habits yet. Use [bold]habit add[/bold] to create one.[/dim]")
        return

    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 1))
    table.add_column("#", style="dim", width=4)
    table.add_column("Habit")
    table.add_column("Category", style="cyan")
    table.add_column("Schedule")
    table.add_column("Target", justify="right")
    table.add_column("Streak", justify="right")
    table.add_column("Today", justify="center")
    table.add_column("Status", justify="left")

    today = date.today()
    for h in habits:
        entries = get_entries(h.id)
        stats = build_stats(h, entries, today=today)
        label = h.label
        cat_str = h.category or "—"
        sched_str = h.schedule or "daily"
        target_str = str(h.target) if h.target else "—"
        streak_str = f"🔥 {stats.current_streak}d" if stats.current_streak > 0 else "—"
        today_str = Text("✓", style="bold green") if stats.done_today else Text("·", style="dim")
        status = Text("archived", style="dim") if h.archived else Text("active", style="green")
        table.add_row(str(h.id), label, cat_str, sched_str, target_str, streak_str, today_str, status)

    console.print(table)


@app.command()
def show(
    name: str = typer.Argument(..., help="Habit name"),
    range_: str = RangeArg,
) -> None:
    """Show heatmap and stats for a habit."""
    from habit_tracker.storage import get_entries
    from habit_tracker.stats import build_stats, range_dates
    from habit_tracker.render.heatmap import render_heatmap
    from habit_tracker.render.stats_panel import render_stats_panel

    h = _require_habit(name)
    since, until = range_dates(range_)
    entries = get_entries(h.id, since=since, until=until)
    all_entries = get_entries(h.id)
    stats = build_stats(h, all_entries, since=since)

    render_heatmap(h, entries, range_name=range_, console=console)
    render_stats_panel(stats, console=console, range_label=range_)


@app.command()
def summary(
    range_: str = RangeArg,
) -> None:
    """Print compact per-habit summary (used by shell startup hook)."""
    from habit_tracker.storage import list_habits, get_entries
    from habit_tracker.stats import build_stats, range_dates
    from habit_tracker.render.summary import render_summary

    try:
        habits = list_habits()
        if not habits:
            return
        since, until = range_dates(range_)
        pairs = []
        today = date.today()
        for h in habits:
            entries = get_entries(h.id)
            stats = build_stats(h, entries, today=today, since=since)
            pairs.append((h, stats))
        render_summary(pairs, console=console, today=today)
    except Exception:
        # Never crash the shell
        pass


@app.command()
def rm(
    name: str = typer.Argument(..., help="Habit name"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
    archive: bool = typer.Option(False, "--archive", help="Archive instead of delete"),
) -> None:
    """Remove or archive a habit."""
    from habit_tracker.storage import delete_habit, archive_habit
    h = _require_habit(name)
    label = h.label

    if archive:
        archive_habit(name)
        console.print(f"[yellow]📦[/yellow] Archived [bold]{label}[/bold]")
        return

    if not force:
        confirmed = typer.confirm(f"Delete habit '{label}' and all its entries?")
        if not confirmed:
            raise typer.Exit(0)

    delete_habit(name)
    console.print(f"[red]✗[/red] Deleted [bold]{label}[/bold]")


@app.command(name="export")
def export_cmd(
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path (default: stdout)"),
    fmt: str = typer.Option("json", "--format", "-f", help="Export format: json | csv"),
) -> None:
    """Export all habits and entries to JSON or CSV."""
    import json
    import csv
    import sys
    from habit_tracker.storage import list_habits, get_entries

    habits = list_habits(include_archived=True)

    if fmt == "csv":
        rows = []
        for h in habits:
            for e in get_entries(h.id):
                rows.append({
                    "habit_name": h.name,
                    "emoji": h.emoji,
                    "target": h.target or "",
                    "date": e.date.isoformat(),
                    "count": e.count,
                    "notes": e.notes or "",
                })
        fieldnames = ["habit_name", "emoji", "target", "date", "count", "notes"]
        if output:
            with open(output, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            console.print(f"[green]✓[/green] Exported {len(rows)} entries to [bold]{output}[/bold]")
        else:
            writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    else:
        data = []
        for h in habits:
            entries = get_entries(h.id)
            data.append({
                "name": h.name,
                "emoji": h.emoji,
                "color": h.color,
                "target": h.target,
                "schedule": h.schedule,
                "category": h.category,
                "created_at": h.created_at.isoformat(),
                "archived": h.archived,
                "entries": [{"date": e.date.isoformat(), "count": e.count, "notes": e.notes} for e in entries],
            })
        payload = json.dumps(data, indent=2)
        if output:
            with open(output, "w") as f:
                f.write(payload)
            console.print(f"[green]✓[/green] Exported {len(data)} habits to [bold]{output}[/bold]")
        else:
            print(payload)


def _import_entry(h, d: date, count: int, notes: str | None, overwrite: bool) -> None:
    """Log a single imported entry, preserving notes and respecting --overwrite."""
    from habit_tracker.storage import get_entry, log_entry
    if overwrite or get_entry(h.id, d) is None:
        log_entry(h.id, d, count=count, notes=notes)


@app.command(name="import")
def import_cmd(
    input_file: str = typer.Argument(..., help="JSON or CSV file to import"),
    fmt: Optional[str] = typer.Option(None, "--format", "-f", help="Import format: json | csv (default: inferred from extension)"),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite existing entries"),
) -> None:
    """Import habits and entries from a JSON or CSV export."""
    import csv
    import json
    from habit_tracker.storage import create_habit, get_habit

    resolved = (fmt or ("csv" if input_file.lower().endswith(".csv") else "json")).lower()
    habit_count = 0

    if resolved == "csv":
        with open(input_file, newline="") as f:
            rows = list(csv.DictReader(f))
        seen: set[str] = set()
        for row in rows:
            name = row["habit_name"]
            h = get_habit(name)
            if h is None:
                target = row.get("target") or None
                h = create_habit(
                    name,
                    emoji=row.get("emoji", ""),
                    target=int(target) if target else None,
                )
            if name not in seen:
                seen.add(name)
                habit_count += 1
            _import_entry(
                h,
                date.fromisoformat(row["date"]),
                int(row.get("count") or 1),
                row.get("notes") or None,
                overwrite,
            )
    else:
        with open(input_file) as f:
            data = json.load(f)
        for item in data:
            h = get_habit(item["name"])
            if h is None:
                h = create_habit(
                    item["name"],
                    emoji=item.get("emoji", ""),
                    color=item.get("color", "green"),
                    target=item.get("target"),
                    schedule=item.get("schedule"),
                    category=item.get("category"),
                )
            for entry in item.get("entries", []):
                _import_entry(
                    h,
                    date.fromisoformat(entry["date"]),
                    entry.get("count", 1),
                    entry.get("notes"),
                    overwrite,
                )
            habit_count += 1

    console.print(f"[green]✓[/green] Imported {habit_count} habits from [bold]{input_file}[/bold]")


@app.command()
def tui() -> None:
    """Launch the interactive TUI."""
    from habit_tracker.tui.app import HabitApp
    HabitApp().run()


@app.command(name="shell-install")
def shell_install(
    remove: bool = typer.Option(False, "--remove", help="Remove the shell hook instead of installing it"),
) -> None:
    """Add (or remove) the habit summary hook in ~/.zshrc."""
    from habit_tracker.shell import install, is_installed, remove as remove_hook
    from pathlib import Path

    rc = Path.home() / ".zshrc"

    if remove:
        removed = remove_hook()
        if removed:
            console.print(f"[yellow]↩[/yellow] Removed habit-tracker hook from [bold]{rc}[/bold]")
        else:
            console.print("[dim]Hook not found — nothing to remove.[/dim]")
        return

    if is_installed():
        console.print(f"[dim]Hook already installed in [bold]{rc}[/bold][/dim]")
        return

    added = install()
    if added:
        console.print(f"[green]✓[/green] Installed startup hook in [bold]{rc}[/bold]")
        console.print("[dim]Open a new terminal to see habit summary on startup.[/dim]")
    else:
        console.print("[dim]Already installed.[/dim]")
