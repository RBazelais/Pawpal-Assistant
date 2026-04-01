from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional

from helpers import format_date  # noqa: F401 — re-exported for convenience

CATEGORIES = [
    "walk",
    "feed",
    "meds",
    "trim nails",
    "bathe",
    "play",
    "train",
    "brush",
    "potty break",
    "teeth brushing",
    "litter box",
    "vet visit",
    "ear cleaning",
]

PRIORITIES = ["low", "medium", "high"]

PRIORITY_RANK = {"low": 1, "medium": 2, "high": 3}

STATUSES = ["pending", "done", "rescheduled", "skipped"]


@dataclass
class Pet:
    name: str
    species: str  # e.g. "dog", "cat", "other"


@dataclass
class Task:
    title: str
    category: str             # one of CATEGORIES
    duration_minutes: int     # 5–90 in 5-min increments
    priority: str             # one of PRIORITIES
    auto_escalate: bool = False       # bump priority after threshold reschedules
    reschedule_count: int = 0         # how many times this task has been pushed back
    last_completed: Optional[date] = None  # date it was last marked done


@dataclass
class Owner:
    name: str
    start_time: str           # e.g. "9:00 AM"
    available_minutes: int    # total minutes available for the day
    reminder_threshold: int = 3    # reschedule count that triggers a reminder
    fill_gaps: bool = False        # if False, stop scheduling when first task doesn't fit


@dataclass
class ScheduledTask:
    task: Task
    start_time: str          # e.g. "9:00 AM", empty string if skipped
    reason: str              # why included or skipped
    status: str = "pending"  # one of STATUSES
    note: str = ""           # optional context, e.g. "Jordan was sick"


@dataclass
class Schedule:
    owner: Owner
    pet: Pet
    date: date               # which day this schedule is for
    items: List[ScheduledTask] = field(default_factory=list)  # all tasks, scheduled + skipped