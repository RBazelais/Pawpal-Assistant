from datetime import date

import streamlit as st

from helpers import format_date
from models import CATEGORIES, PRIORITIES, Owner, Pet, Task
from scheduler import build_schedule

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.markdown("Plan your pet's day — biology first, flexibility always.")

st.divider()

# --- Owner Setup ---
st.subheader("Owner Info")
col1, col2 = st.columns(2)
with col1:
    owner_name = st.text_input("Your name", value="Jordan")
with col2:
    pet_name = st.text_input("Pet name", value="Mochi")

species = st.selectbox("Species", ["dog", "cat", "other"])

st.subheader("Schedule Settings")
col1, col2 = st.columns(2)
with col1:
    start_time = st.selectbox(
        "Start time",
        [f"{h}:{m:02d} {'AM' if h < 12 else 'PM'}" for h in range(6, 13) for m in (0, 30)]
        + [f"{h}:{m:02d} PM" for h in range(1, 7) for m in (0, 30)],
        index=6,  # default 9:00 AM
    )
with col2:
    available_minutes = st.select_slider(
        "Available time (minutes)",
        options=list(range(30, 181, 15)),
        value=90,
    )

col1, col2 = st.columns(2)
with col1:
    reminder_threshold = st.number_input(
        "Remind me if a task is rescheduled this many times",
        min_value=1, max_value=10, value=3
    )
with col2:
    fill_gaps = st.toggle("Fill gaps (keep scheduling after a task doesn't fit)", value=False)

st.divider()

# --- Task Builder ---
st.subheader("Tasks")
st.caption("Add tasks for today. Priority and category determine the order.")

if "tasks" not in st.session_state:
    st.session_state.tasks = []

col1, col2 = st.columns(2)
with col1:
    task_title = st.text_input("Task title", placeholder="Name your task")
with col2:
    category = st.selectbox("Category", ["Select task type"] + CATEGORIES)

col1, col2, col3 = st.columns(3)
with col1:
    duration = st.select_slider(
        "Duration (min)", options=list(range(5, 91, 5)), value=20
    )
with col2:
    priority = st.selectbox("Priority", PRIORITIES, index=1)
with col3:
    auto_escalate = st.toggle("Auto-escalate priority", value=False)

if st.button("Add task"):
    if not task_title.strip():
        st.warning("Please name your task.")
    elif category == "Select task type":
        st.warning("Please select a task type.")
    else:
        st.session_state.tasks.append(
            Task(
                title=task_title,
                category=category,
                duration_minutes=int(duration),
                priority=priority,
                auto_escalate=auto_escalate,
            )
        )
        st.rerun()

if st.session_state.tasks:
    st.write("Current tasks:")
    st.table([
        {
            "Title": t.title,
            "Category": t.category,
            "Duration": f"{t.duration_minutes} min",
            "Priority": t.priority,
            "Auto-escalate": "Yes" if t.auto_escalate else "No",
        }
        for t in st.session_state.tasks
    ])
    if st.button("Clear all tasks"):
        st.session_state.tasks = []
        st.rerun()
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# --- Generate Schedule ---
st.subheader("Generate Schedule")

if st.button("Build today's schedule", type="primary"):
    if not st.session_state.tasks:
        st.warning("Add at least one task first.")
    else:
        owner = Owner(
            name=owner_name,
            start_time=start_time,
            available_minutes=available_minutes,
            reminder_threshold=reminder_threshold,
            fill_gaps=fill_gaps,
        )
        pet = Pet(name=pet_name, species=species)
        schedule = build_schedule(owner, pet, st.session_state.tasks, date.today())

        scheduled = [i for i in schedule.items if i.status == "pending"]
        skipped = [i for i in schedule.items if i.status == "skipped"]

        st.success(f"Schedule for {pet.name} — {format_date(schedule.date)}")
        st.caption(f"{owner.name} · Starting {owner.start_time} · {owner.available_minutes} min available")

        # --- Today's Plan ---
        st.markdown("### Today's Plan")
        if scheduled:
            for item in scheduled:
                with st.expander(f"🕐 {item.start_time} — {item.task.title} ({item.task.duration_minutes} min)"):
                    st.markdown(f"**Category:** {item.task.category}")
                    st.markdown(f"**Priority:** {item.task.priority}")
                    st.markdown(f"**Why:** {item.reason}")
        else:
            st.info("No tasks fit within the available time.")

        # --- Didn't Make the Cut ---
        if skipped:
            st.markdown("### Didn't Make the Cut")
            for item in skipped:
                with st.expander(f"⏭️ {item.task.title} ({item.task.duration_minutes} min)"):
                    st.markdown(f"**Category:** {item.task.category}")
                    st.markdown(f"**Priority:** {item.task.priority}")
                    st.markdown(f"**Reason:** {item.reason}")