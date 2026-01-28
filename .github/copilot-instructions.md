# Copilot Instructions for Paint Controller

## Project Overview

ROS2 node with PySide6/QML UI for robotic paint controller on Steam Deck. Hybrid Python + C++ codebase.

**Stack**: ROS2 (Humble/Jazzy), Python 3.10+, PySide6, QML, C++

**Key Paths**:
- `python/paint_controller/` — Main Python application
- `python/paint_controller/qml/` — QML UI components
- `src/` — C++ nodes
- `launch/` — ROS2 launch files

## Build & Run

```bash
# Build ROS2 packages
cd ~/ros2_ws && colcon build --packages-select paint_interfaces paint_controller_ros2

# Run application
paint_controller
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

Before merging PR, MUST delete `PLANNING.md`. This file is temporary and should not be committed to main branch.

---

### Stop and Ask Triggers

You MUST pause and ask for explicit guidance before:

- **Deleting any file**
- **Modifying launch files** (`launch/*.py`)
- **Changing ROS2 message types** or service definitions
- **Modifying CMakeLists.txt or package.xml**
- **Any change rated High complexity**

---

### Planning Example

```markdown
## Task: Fix joystick deadzone not persisting

**Understanding**: Joystick deadzone resets to default when switching controller modes
**Complexity**: Medium
**KNOWLEDGE.md Check**: "Signal Timing" — Python signals may fire before Qt state updates

**File Classification**:
- [x] Python signal handler → identified async boundaries

**Affected Files**:
- `python/paint_controller/handlers/input.py` — deadzone state management
  - Callers: MainWindow.qml (mode switch buttons)
  - Callees: settings.py (persistence layer)
- `python/paint_controller/core/settings.py` — verify save/load timing

**Cross-Layer Impact**: QML↔Python (mode switch signal triggers Python handler)

**Approach**:
1. Trace where deadzone is initialized vs loaded from settings
2. Check if mode switch resets state before settings load completes
3. Add explicit load after mode switch, or preserve state across switches

**Risks**: Other input settings might have same issue
**Rollback Plan**: Revert input.py changes; deadzone will reset but app functional
```

---

## DEVNOTES.md Rules

Development notes track what was tried, issues encountered, and solutions found.

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
4. **Size limit**: If file exceeds 1500 lines, ask user before deleting oldest entries

### Example Entry

```markdown
### 2026-01-19 14:30 - Fix Screen Detection Timing

**Goal**: Update UI when monitors connected/disconnected
**Issues**: `Qt.application.screens` had stale data when Python signal fired
**Tried**: Direct property binding → failed; immediate refresh → failed
**Result**: ✅ 100ms Timer delay lets Qt update internal state first
**Files**: `qml/core/MainWindow.qml`
```

---

## KNOWLEDGE.md Rules

Reusable learnings extracted from DEVNOTES.md for future reference.

### When to Add

After completing a DEVNOTES entry, evaluate:
- Is this a reusable pattern or gotcha?
- Would this help avoid the same mistake in future?
- Is it project-agnostic or broadly applicable?

**Always ask user for confirmation before adding to KNOWLEDGE.md.**

### Format

Short title + 2-4 line explanation. Group by category.

---

## General Rules

1. **No standalone documentation files** unless user explicitly requests
2. **Check KNOWLEDGE.md** before debugging — solution may already exist
3. **Update DEVNOTES.md** after significant debugging sessions or feature work
