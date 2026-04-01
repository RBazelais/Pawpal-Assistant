from datetime import date

import pytest

from models import Owner, Pet, Task
from scheduler import build_schedule

TODAY = date(2026, 3, 31)


def make_owner(available_minutes=60, fill_gaps=False, reminder_threshold=3):
    return Owner(
        name="Jordan",
        start_time="9:00 AM",
        available_minutes=available_minutes,
        reminder_threshold=reminder_threshold,
        fill_gaps=fill_gaps,
    )


def make_pet():
    return Pet(name="Mochi", species="dog")


# --- Test 1: High priority tasks appear before low priority tasks ---

def test_priority_ordering():
    tasks = [
        Task(title="Trim nails", category="trim nails", duration_minutes=15, priority="low"),
        Task(title="Give meds", category="meds", duration_minutes=5, priority="high"),
    ]
    schedule = build_schedule(make_owner(), make_pet(), tasks, TODAY)
    scheduled = [i for i in schedule.items if i.status == "pending"]

    assert scheduled[0].task.title == "Give meds"
    assert scheduled[1].task.title == "Trim nails"


# --- Test 2: Tasks that don't fit are marked skipped ---

def test_time_constraint_skips_long_tasks():
    tasks = [
        Task(title="Feed Mochi", category="feed", duration_minutes=10, priority="high"),
        Task(title="Bath time", category="bathe", duration_minutes=60, priority="high"),
    ]
    schedule = build_schedule(make_owner(available_minutes=30), make_pet(), tasks, TODAY)

    statuses = {i.task.title: i.status for i in schedule.items}
    assert statuses["Feed Mochi"] == "pending"
    assert statuses["Bath time"] == "skipped"


# --- Test 3: fill_gaps=False stops after first task that doesn't fit ---

def test_fill_gaps_false_stops_scheduling():
    # All high priority — sorted by category rank: meds(2) → brush(6) → play(7)
    # meds fits, brush doesn't, play would fit but fill_gaps=False so it stops
    tasks = [
        Task(title="Give meds", category="meds", duration_minutes=5, priority="high"),
        Task(title="Brush Mochi", category="brush", duration_minutes=30, priority="high"),
        Task(title="Playtime", category="play", duration_minutes=10, priority="high"),
    ]
    # 25 min available: meds(5) fits → 20 left, brush(30) doesn't → stop, play skipped
    schedule = build_schedule(make_owner(available_minutes=25, fill_gaps=False), make_pet(), tasks, TODAY)

    statuses = {i.task.title: i.status for i in schedule.items}
    assert statuses["Give meds"] == "pending"
    assert statuses["Brush Mochi"] == "skipped"
    assert statuses["Playtime"] == "skipped"


# --- Test 4: Auto-escalate bumps priority after hitting threshold ---

def test_auto_escalate_bumps_priority():
    task = Task(
        title="Trim nails",
        category="trim nails",
        duration_minutes=15,
        priority="low",
        auto_escalate=True,
        reschedule_count=3,  # hits the default threshold of 3
    )
    schedule = build_schedule(make_owner(reminder_threshold=3), make_pet(), [task], TODAY)

    # Priority should have been bumped to medium before scheduling
    assert schedule.items[0].task.priority == "medium"


# --- Test 5: Category rank breaks ties within same priority ---

def test_category_rank_tiebreaker():
    tasks = [
        Task(title="Give meds", category="meds", duration_minutes=5, priority="high"),
        Task(title="Feed Mochi", category="feed", duration_minutes=5, priority="high"),
    ]
    schedule = build_schedule(make_owner(), make_pet(), tasks, TODAY)
    scheduled = [i for i in schedule.items if i.status == "pending"]

    # Feed (rank 1) should come before meds (rank 2)
    assert scheduled[0].task.title == "Feed Mochi"
    assert scheduled[1].task.title == "Give meds"