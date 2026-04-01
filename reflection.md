# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

We designed four core classes before writing any logic:

- `Pet` — holds the pet's name and species. Kept simple intentionally; the scheduler cares about tasks, not the animal's details.
- `Task` — the unit of work. Has a title, category (from a fixed list of 13 care types), duration in 5-min increments (5–90 min), and a priority level (low/medium/high).
- `Owner` — represents the person planning the day. Has a name, a start time (e.g. "9:00 AM"), and total available minutes for the day.
- `ScheduledTask` — a wrapper around a Task that adds a computed start time and a human-readable reason explaining why it was included.
- `Schedule` — the output of the scheduler. Holds an ordered list of `ScheduledTask` items and a list of skipped tasks with reasons.

Priority is stored as a string (`low/medium/high`) with a `PRIORITY_RANK` dict mapping to integers for sorting. Duration is always a multiple of 5 minutes, enforced by the UI.

**b. Design changes**

Before writing any logic, we expanded `ScheduledTask` to include `status` and `note` fields. The original design only tracked whether a task was in the schedule or skipped — but real users don't always complete their plans. Life gets in the way.

Adding `status` (`pending`, `done`, `rescheduled`, `skipped`) and an optional `note` field (e.g. "Jordan was sick") means a generated schedule can be edited after the fact. Rescheduled tasks can be collected and fed into a new day's plan. This flexibility was a deliberate design choice made before the scheduler was built — not patched in later — because it affects the shape of the output data.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The sorting logic is biology first. Tasks are sorted by three levels:

1. **Priority** (high → low) — the owner's stated urgency comes first
2. **Category rank** — within the same priority, biological needs take precedence. Feed before meds, meds before potty break, daily care before periodic grooming. A pet's basic needs aren't negotiable.
3. **Duration** (shortest first) — within the same priority and category, shorter tasks go first to maximize how many things get done

A fourth constraint is reschedule history — tasks with `auto_escalate = True` have their priority bumped before sorting if they've been pushed back past the owner's `reminder_threshold`. This means neglected tasks naturally rise in the schedule over time without the owner having to remember to reprioritize them.

**b. Tradeoffs**

Three tradeoffs were decided during data modeling:

1. **History on `Task` vs. a separate log.** `reschedule_count` and `last_completed` live directly on `Task` for simplicity. The tradeoff is that we can't see the full history of when something was rescheduled — just the count. This is acceptable for now but would need a dedicated log if we ever add detailed analytics.

2. **Skipped tasks in one list.** Rather than maintaining a separate `skipped` list, all tasks (scheduled and skipped) live in `Schedule.items` distinguished by `status`. This makes rescheduling consistent — any item can be acted on the same way — and the UI handles the visual separation.

3. **`datetime.date` over strings.** Dates use `datetime.date` so the app can do time-based math (e.g. days since last completed, week-over-week reschedule patterns). A `format_date()` helper handles display conversion.

4. **`fill_gaps` defaults to False.** When a task doesn't fit, the scheduler stops rather than scanning ahead for smaller tasks that might fit. The default gives owners breathing room — both owners and pets need buffer between tasks, and an overpacked schedule is harder to stick to. Owners can opt in to gap-filling if they want a denser day, but that choice is theirs to make.

---

## 3. AI Collaboration

**a. How you used AI**

AI was used as a senior engineering mentor throughout — not to generate code blindly, but to think through design decisions together before writing anything. The most useful interactions were conversational: talking through tradeoffs (fill_gaps, skipped task structure, date types), designing the category ranking collaboratively, and walking through the scheduler logic piece by piece before it was written.

**b. Judgment and verification**

When AI suggested `auto_escalate` as a global setting on `Owner`, we pushed back — everyday tasks like feed and walk shouldn't escalate, but periodic tasks like trim nails should be able to opt in. That distinction came from thinking about the real user, not the data model. The AI accepted the correction and updated the design. We also caught a failing test where the test itself was wrong (not the scheduler), which confirmed the sort logic was working correctly rather than masking a bug by fixing the wrong thing.

---

## 4. Testing and Verification

**a. What you tested**

Five behaviors were tested:

1. **Priority ordering** — high priority tasks appear before low priority ones
2. **Time constraint** — tasks that exceed remaining time are marked skipped
3. **fill_gaps=False** — scheduling stops after the first task that doesn't fit; remaining tasks are skipped even if they would fit
4. **Auto-escalate** — a task's priority bumps up one level when reschedule_count hits the owner's reminder_threshold
5. **Category rank tiebreaker** — when two tasks share the same priority, the one with a lower category rank (more biologically urgent) is scheduled first

These tests matter because they cover the three-level sort, the time constraint, and the two owner-configurable behaviors (fill_gaps and auto_escalate). If any of these break, the schedule will be wrong in ways the owner might not notice.

**b. Confidence**

The core scheduling logic is well covered. One test initially failed because the test assumed a wrong task order — the scheduler correctly sorted by priority before category rank, which the test didn't account for. Catching and fixing that revealed the sort is working as designed.

Edge cases to test next: empty task list, all tasks skipped, owner with 0 available minutes, a task already at "high" priority being auto-escalated.

---

## 5. Reflection

**a. What went well**

The flexibility built into the application. Owners can skip tasks, reschedule them, leave notes for why something didn't happen, and the system handles it gracefully without breaking. That flexibility was designed in from the start, not bolted on later.

**b. What you would improve**

Full CRUD — adding edit and delete for individual tasks would complete the task management experience. The other big addition would be calendar export so a generated schedule could go straight into Google Calendar or Apple Calendar. Right now the plan lives only in the app.

**c. Key takeaway**

You need to account for when people won't do what you expect. Users skip things, run out of time, get sick, change their minds. A system that only works when everything goes according to plan isn't useful. The rescheduling, status tracking, and fill_gaps decisions all came from asking "what happens when the user doesn't follow the golden path?"
