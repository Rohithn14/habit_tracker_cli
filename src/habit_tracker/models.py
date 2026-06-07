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
    schedule: str | None = None
    category: str | None = None

    @property
    def label(self) -> str:
        """Display name with the emoji prefix when one is set."""
        return f"{self.emoji} {self.name}" if self.emoji else self.name


@dataclass
class Entry:
    habit_id: int
    date: date
    count: int = 1
    notes: str | None = None


@dataclass
class HabitStats:
    habit: Habit
    current_streak: int
    longest_streak: int
    completion_rate: float
    total_completions: int
    done_today: bool
    today_count: int = 0
    entries: list[Entry] = field(default_factory=list)
    rolling_completion: list[float] = field(default_factory=list)
    day_of_week_bias: dict[int, float] = field(default_factory=dict)
