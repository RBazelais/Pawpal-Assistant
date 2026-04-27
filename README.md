# PawPal+

A Streamlit app that helps pet owners plan daily care tasks and ask general pet care questions powered by a RAG-based AI assistant.

## Demo

> Watch a walkthrough of the scheduler and Ask PawPal assistant:

[Insert Loom link here]

**Example questions shown in the demo:**

- "How often should I brush my dog?" - green Answer badge with source
- "My cat has an upset stomach and vomits after eating" - green Answer badge with pumpkin puree advice
- "What plants are toxic for cats?" - green Answer badge with sourced list
- "What medication can I give my dog for pain?" - red See a vet badge (no API call made)

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## System Architecture

### Ask PawPal — Decision Flow

```mermaid
flowchart TD
    A([User asks a question]) --> B[Triage: keyword blocklist]

    B -->|symptom / medication / injury| VET([🔴 See a vet])

    B -->|no red flags| C[Species check]
    C -->|exotic / other| IDK([🟡 I don't know enough])

    C -->|dog or cat| D[RAG retrieval\nTF-IDF similarity]
    D -->|score below threshold| IDK

    D -->|score above threshold| E[LLM — grounded\non retrieved context]
    E --> ANS([🟢 Answer with source])
```

### Scheduler — Data Model

```mermaid
classDiagram
    class Owner {
        +str name
        +str start_time
        +int available_minutes
        +int reminder_threshold
        +bool fill_gaps
    }
    class Pet {
        +str name
        +str species
    }
    class Task {
        +str title
        +str category
        +int duration_minutes
        +str priority
        +bool auto_escalate
        +int reschedule_count
        +date last_completed
    }
    class ScheduledTask {
        +Task task
        +str start_time
        +str reason
        +str status
        +str note
    }
    class Schedule {
        +Owner owner
        +Pet pet
        +date date
        +list items
    }

    Schedule --> Owner
    Schedule --> Pet
    Schedule "1" --> "many" ScheduledTask
    ScheduledTask --> Task
```

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
