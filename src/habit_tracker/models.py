from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class Habit:
    id: int
    name: str
    emoji: str
    color: str
    target: int | None
    created_at: date
    archived: bool = False


@dataclass
class Entry:
    habit_id: int
    date: date
    count: int = 1


@dataclass
class HabitStats:
    habit: Habit
    current_streak: int
    longest_streak: int
    completion_rate: float
    total_completions: int
    done_today: bool
    entries: list[Entry] = field(default_factory=list)
