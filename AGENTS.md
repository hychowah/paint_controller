# Agent Instructions — Paint Controller

> **Start every session by reading `INDEX.md` first.** It gives orientation, the read-order checklist, and the authority hierarchy.

---

## Project Overview

ROS2 node with PySide6/QML UI for robotic paint controller on Steam Deck. Python-first codebase; the historical C++ UI path has been removed from the live tree.

**Stack**: ROS2 (Humble/Jazzy), Python 3.10+, PySide6, QML

**Key Paths**:
- `python/paint_controller/` — Main Python application
- `python/paint_controller/qml/` — QML UI components
- `launch/` — ROS2 launch files

## Build & Run

```bash
# Build ROS2 packages
cd ~/ros2_ws && colcon build --packages-select paint_interfaces paint_controller_ros2

# Run application
paint_controller

# Run tests
python/paint_controller/venv/bin/python -m pytest tests -q
```

---

## Planning Before Implementation (REQUIRED)

You MUST follow this workflow for ALL tasks. NEVER modify code before completing the Plan phase and receiving user confirmation.

### Phase 1: Understand

1. **Restate the problem** in your own words
2. **Check KNOWLEDGE.md** for related patterns or gotchas
3. **Classify the change type**:
   - UI/Display → extra caution for Qt timing, layout rules
   - State management → trace full state flow first
   - Hardware control → verify controller abstraction exists
4. **Identify all affected files and components**
5. **Trace dependencies** — list callers/callees for any modified function

### Phase 2: Plan

Create or update `PLANNING.md` in the repository root with this template:

```markdown
## Task: [Brief title]

**Understanding**: [Restate the problem]
**Complexity**: Low | Medium | High
**KNOWLEDGE.md Check**: [Relevant entries found, or "None applicable"]

**File Classification**:
- [ ] QML component → checked layout rules, property conflicts
- [ ] Python signal handler → identified async boundaries
- [ ] ROS2/Hardware → verified controller abstraction

**Affected Files**:
- `path/to/file.py` — [what changes needed]
  - Callers: [functions/components that call this]
  - Callees: [functions/components this calls]

**Cross-Layer Impact**: [None | QML↔Python | Python↔ROS2 | describe boundary]

**Approach**: [High-level strategy, step by step]
**Risks**: [Potential issues or breaking changes]
**Rollback Plan**: [How to revert if broken] *(required for Medium/High complexity)*
```

### Phase 3: Confirm

MUST ask user: **"Here is my plan in PLANNING.md. Ready to proceed?"**

NEVER start implementation without explicit user approval.

### Phase 4: Implement

Make changes one logical unit at a time. Update DEVNOTES.md if significant debugging or learning occurred.

### Phase 5: Cleanup

`PLANNING.md` is temporary local scratch state. Keep it current while working, but do not treat it as a branch/merge blocker because it is gitignored.

---

## Stop and Ask Triggers

You MUST pause and ask for explicit guidance before:

- **Deleting any file**
- **Modifying launch files** (`launch/*.py`)
- **Changing ROS2 message types** or service definitions
- **Modifying CMakeLists.txt or package.xml**
- **Any change rated High complexity**

---

## DEVNOTES.md Rules

Development notes track what was tried, issues encountered, and solutions found. DEVNOTES is an **inbox**, not an archive.

### Format

```markdown
### YYYY-MM-DD HH:MM - [Feature/Bug Title]

**Goal**: What we tried to accomplish
**Issues**: Problems encountered
**Tried**: Solutions attempted
**Result**: What worked / what didn't
**Files**: Modified files (if relevant)
```

### Guidelines

1. **Be concise** — Focus on actionable information
2. **One timestamp per feature/session** — Group related work together
3. **Code snippets**: Keep short (3-5 lines), show before/after pattern

### Rotation Policy (90-day rolling window)

DEVNOTES entries have a maximum age of **90 days**. Older entries must be triaged and rotated out.

**Rotation trigger**: Any entry older than 90 days, OR file exceeds ~300 lines.

**Triage steps** (for each entry older than 90 days):
1. Read the entry fully
2. Does it contain a reusable pattern, gotcha, anti-pattern, or design decision not yet in KNOWLEDGE.md?
   - Yes → propose the extracted entry to the user for confirmation, then add to KNOWLEDGE.md
   - No → proceed to step 3
3. Move the full entry verbatim to `docs/devnotes/YYYY-QN.md` (quarterly archive):
   - Q1 = Jan–Mar, Q2 = Apr–Jun, Q3 = Jul–Sep, Q4 = Oct–Dec
   - Create the file if it does not exist
4. Remove the entry from DEVNOTES.md

**What to extract → KNOWLEDGE.md**: gotchas, design decisions, anti-patterns, timing rules, discovered constraints

**What to archive only**: step-by-step implementation narratives, file lists, "tried X failed" detail

**What git handles** (do not duplicate in DEVNOTES): exact line changes, before/after code diffs

---

## KNOWLEDGE.md Rules

Reusable learnings extracted from DEVNOTES.md or discovered during debugging.

### When to Add

After completing a DEVNOTES entry, evaluate:
- Is this a reusable pattern or gotcha?
- Would this help avoid the same mistake in future?
- Is it broadly applicable beyond this specific feature?

**Always ask user for confirmation before adding to KNOWLEDGE.md.**

### Format

Short title + 2-4 line explanation. Group by category.

---

## General Rules

1. **No standalone documentation files** unless user explicitly requests
2. **Check KNOWLEDGE.md** before debugging — solution may already exist
3. **Update DEVNOTES.md** after significant debugging sessions or feature work
4. **INDEX.md is the session-start map** — consult it in any fresh session before any other file
5. **Update `docs/tech-debt.md`** when new debt is discovered or existing items are resolved — move resolved items to the Resolved table with date and one-line note
