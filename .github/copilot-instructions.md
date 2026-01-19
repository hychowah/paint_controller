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
