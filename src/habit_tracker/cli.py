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

RangeArg = typer.Option("year", "--range", "-r", help="Time range: year | quarter | month")


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
) -> None:
    """Create a new habit."""
    from habit_tracker.storage import create_habit, get_habit
    if get_habit(name):
        err_console.print(f"[yellow]Habit '[bold]{name}[/bold]' already exists.[/yellow]")
        raise typer.Exit(1)
    h = create_habit(name, emoji=emoji, color=color, target=target)
    label = f"{h.emoji} {h.name}" if h.emoji else h.name
    console.print(f"[green]✓[/green] Created habit [bold]{label}[/bold]" + (f" (target: {target}/day)" if target else ""))


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
    label = f"{h.emoji} {h.name}" if h.emoji else h.name
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
    label = f"{h.emoji} {h.name}" if h.emoji else h.name

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
    label = f"{h.emoji} {h.name}" if h.emoji else h.name
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
    table.add_column("Target", justify="right")
    table.add_column("Streak", justify="right")
    table.add_column("Today", justify="center")
    table.add_column("Status", justify="left")

    today = date.today()
    for h in habits:
        entries = get_entries(h.id)
        stats = build_stats(h, entries, today=today)
        label = f"{h.emoji} {h.name}" if h.emoji else h.name
        target_str = str(h.target) if h.target else "—"
        streak_str = f"🔥 {stats.current_streak}d" if stats.current_streak > 0 else "—"
        today_str = Text("✓", style="bold green") if stats.done_today else Text("·", style="dim")
        status = Text("archived", style="dim") if h.archived else Text("active", style="green")
        table.add_row(str(h.id), label, target_str, streak_str, today_str, status)

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
    render_stats_panel(stats, console=console)


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
    label = f"{h.emoji} {h.name}" if h.emoji else h.name

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


@app.command(name="import")
def import_cmd(
    input_file: str = typer.Argument(..., help="JSON file to import"),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite existing entries"),
) -> None:
    """Import habits and entries from a JSON export."""
    import json
    from habit_tracker.storage import create_habit, get_habit, log_entry

    with open(input_file) as f:
        data = json.load(f)

    imported = 0
    for item in data:
        h = get_habit(item["name"])
        if h is None:
            h = create_habit(
                item["name"],
                emoji=item.get("emoji", ""),
                color=item.get("color", "green"),
                target=item.get("target"),
            )
        for entry in item.get("entries", []):
            d = date.fromisoformat(entry["date"])
            if overwrite:
                log_entry(h.id, d, count=entry.get("count", 1))
            else:
                from habit_tracker.storage import get_entry
                if get_entry(h.id, d) is None:
                    log_entry(h.id, d, count=entry.get("count", 1))
        imported += 1

    console.print(f"[green]✓[/green] Imported {imported} habits from [bold]{input_file}[/bold]")


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
