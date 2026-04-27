from datetime import date

import streamlit as st

from assistant import ask
from helpers import format_date
from models import CATEGORIES, PRIORITIES, Owner, Pet, Task
from scheduler import build_schedule

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.markdown("Plan your pet's day — biology first, flexibility always.")

tab_scheduler, tab_assistant = st.tabs(["📅 Scheduler", "💬 Ask PawPal"])

# ---------------------------------------------------------------------------
# TAB 1 — Scheduler (unchanged)
# ---------------------------------------------------------------------------
with tab_scheduler:
    st.divider()

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
            index=6,
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
            min_value=1, max_value=10, value=3,
        )
    with col2:
        fill_gaps = st.toggle("Fill gaps (keep scheduling after a task doesn't fit)", value=False)

    st.divider()

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

            st.markdown("### Today's Plan")
            if scheduled:
                for item in scheduled:
                    with st.expander(f"🕐 {item.start_time} — {item.task.title} ({item.task.duration_minutes} min)"):
                        st.markdown(f"**Category:** {item.task.category}")
                        st.markdown(f"**Priority:** {item.task.priority}")
                        st.markdown(f"**Why:** {item.reason}")
            else:
                st.info("No tasks fit within the available time.")

            if skipped:
                st.markdown("### Didn't Make the Cut")
                for item in skipped:
                    with st.expander(f"⏭️ {item.task.title} ({item.task.duration_minutes} min)"):
                        st.markdown(f"**Category:** {item.task.category}")
                        st.markdown(f"**Priority:** {item.task.priority}")
                        st.markdown(f"**Reason:** {item.reason}")


# ---------------------------------------------------------------------------
# TAB 2 — Ask PawPal
# ---------------------------------------------------------------------------
_BADGE = {
    "ANSWER": ("green",  "Answer"),
    "IDK":    ("orange", "Not sure"),
    "VET":    ("red",    "See a vet"),
}

with tab_assistant:
    st.markdown("Ask a general care question about your pet.")
    st.caption("Medical symptoms, medications, and injuries are always referred to a vet.")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    col1, col2 = st.columns([3, 1])
    with col1:
        user_query = st.chat_input("Ask PawPal a question…")
    with col2:
        ask_species = st.selectbox(
            "Species",
            ["dog", "cat", "other"],
            key="ask_species",
            label_visibility="collapsed",
        )

    # Render existing chat history.
    for entry in st.session_state.chat_history:
        with st.chat_message("user"):
            st.write(entry["query"])
        with st.chat_message("assistant"):
            color, label = _BADGE[entry["outcome"]]
            st.markdown(
                f'<span style="background:{color};color:white;'
                f'padding:2px 8px;border-radius:4px;font-size:0.75rem;">'
                f'{label}</span> '
                f'<span style="color:grey;font-size:0.75rem;">'
                f'confidence: {entry["confidence"]:.0%}</span>',
                unsafe_allow_html=True,
            )
            st.write(entry["response"])
            if entry["sources"]:
                st.caption("Sources: " + ", ".join(entry["sources"]))

    # Process new question.
    if user_query:
        with st.chat_message("user"):
            st.write(user_query)

        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                result = ask(user_query, species=ask_species)

            color, label = _BADGE[result["outcome"]]
            st.markdown(
                f'<span style="background:{color};color:white;'
                f'padding:2px 8px;border-radius:4px;font-size:0.75rem;">'
                f'{label}</span> '
                f'<span style="color:grey;font-size:0.75rem;">'
                f'confidence: {result["confidence"]:.0%}</span>',
                unsafe_allow_html=True,
            )
            st.write(result["response"])
            if result["sources"]:
                st.caption("Sources: " + ", ".join(result["sources"]))

        st.session_state.chat_history.append(
            {
                "query": user_query,
                "outcome": result["outcome"],
                "response": result["response"],
                "confidence": result["confidence"],
                "sources": result["sources"],
            }
        )
