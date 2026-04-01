from datetime import date

from helpers import add_minutes
from models import (
    PRIORITIES,
    PRIORITY_RANK,
    Owner,
    Pet,
    Schedule,
    ScheduledTask,
    Task,
)

# Lower number = scheduled earlier in the day.
# Biological needs first, periodic grooming last.
CATEGORY_RANK = {
    "feed": 1,
    "meds": 2,
    "potty break": 3,
    "litter box": 4,
    "walk": 5,
    "brush": 6,
    "play": 7,
    "train": 8,
    "teeth brushing": 9,
    "ear cleaning": 10,
    "trim nails": 11,
    "bathe": 12,
    "vet visit": 13,
}


def _escalate_priority(task: Task) -> None:
    # Bump a task's priority up one level if auto_escalate is on and it qualifies
    if not task.auto_escalate:
        return
    current = PRIORITIES.index(task.priority)
    if current < len(PRIORITIES) - 1:
        task.priority = PRIORITIES[current + 1]


def build_schedule(
    owner: Owner,
    pet: Pet,
    tasks: list[Task],
    schedule_date: date,
) -> Schedule:
    # Step 1 — escalate priority for any overdue tasks before sorting
    for task in tasks:
        if task.reschedule_count >= owner.reminder_threshold:
            _escalate_priority(task)

    # Step 2 — sort: high priority first, then category order, then shortest first
    sorted_tasks = sorted(
        tasks,
        key=lambda t: (
            -PRIORITY_RANK[t.priority],
            CATEGORY_RANK.get(t.category, 99),
            t.duration_minutes,
        ),
    )

    # Step 3 — walk through tasks, assign time slots
    schedule = Schedule(owner=owner, pet=pet, date=schedule_date)
    current_time = owner.start_time
    time_remaining = owner.available_minutes

    for task in sorted_tasks:
        fits = task.duration_minutes <= time_remaining

        if fits:
            # Build a reason explaining why this task made the schedule
            reason = f"Priority: {task.priority}. Fits within available time ({task.duration_minutes} min)."
            if task.reschedule_count >= owner.reminder_threshold:
                reason += f" Reminder: this task has been rescheduled {task.reschedule_count} time(s)."

            schedule.items.append(
                ScheduledTask(
                    task=task,
                    start_time=current_time,
                    reason=reason,
                    status="pending",
                )
            )

            current_time = add_minutes(current_time, task.duration_minutes)
            time_remaining -= task.duration_minutes

        else:
            # Build a reason explaining why it was skipped
            reason = (
                f"Not enough time remaining ({time_remaining} min left, "
                f"task needs {task.duration_minutes} min)."
            )
            if task.reschedule_count >= owner.reminder_threshold:
                reason += f" Reminder: this task has been rescheduled {task.reschedule_count} time(s) — consider prioritizing it tomorrow."

            schedule.items.append(
                ScheduledTask(
                    task=task,
                    start_time="",
                    reason=reason,
                    status="skipped",
                )
            )

            # If owner prefers no gap-filling, stop scheduling after first miss
            if not owner.fill_gaps:
                # Mark all remaining tasks as skipped too
                remaining = sorted_tasks[sorted_tasks.index(task) + 1:]
                for remaining_task in remaining:
                    schedule.items.append(
                        ScheduledTask(
                            task=remaining_task,
                            start_time="",
                            reason="Scheduling stopped after available time was reached.",
                            status="skipped",
                        )
                    )
                break

    return schedule