# Agent Instructions — Paint Controller

> **Start every session by reading `INDEX.md` first.** It gives orientation, the read-order checklist, and the authority hierarchy.

---

## Project Overview

ROS2 node with PySide6/QML UI for robotic paint controller on a Steam Deck. Python-first codebase; the historical C++ UI path has been removed from the live tree.

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

## Kimi CLI Tool Mapping

Use the current Kimi CLI tools to implement the workflow below with less friction and better accountability:

| Tool | Use it when |
|---|---|
| `EnterPlanMode` / `ExitPlanMode` | Any non-trivial task (new feature, refactor, multi-file change, or anything rated Medium/High). Enter before exploring, write the plan to `PLANNING.md`, then exit for user approval. |
| `TodoList` | The task has more than two discrete steps, spans multiple files, or requires tracking investigation → implementation → verification. |
| `Agent` / `AgentSwarm` | You need more than three searches to understand a code path, or you can safely parallelize independent investigations (e.g. trace state flow in Python while another agent traces QML consumers). |
| `AskUserQuestion` | A requirement is ambiguous, multiple valid approaches exist, or you hit a stop-and-ask trigger. Use structured options; do not use it for "is this OK?" — that is what `ExitPlanMode` is for. |
| `CreateGoal` / `GetGoal` | The user explicitly asks you to work autonomously toward an outcome that spans multiple turns and has a clear, checkable finish line. |
| `CronCreate` | The user asks for a recurring check or one-shot reminder tied to time. Not for normal implementation work. |

Default to the simplest tool that fits. Do not spin up subagents for trivial one-file reads or single-line fixes.

---

## Planning Before Implementation (REQUIRED)

You MUST follow this workflow for ALL tasks. NEVER modify code before completing the Plan phase and receiving user confirmation.

### Phase 1: Understand

1. **Restate the problem** in your own words.
2. **Check `KNOWLEDGE.md`** for related patterns or gotchas.
3. **Classify the change type**:
   - UI/Display → extra caution for Qt timing, layout rules
   - State management → trace full state flow first
   - Hardware control → verify controller abstraction exists
4. **Identify all affected files and components**.
5. **Trace dependencies** — list callers/callees for any modified function.

> For broad or unfamiliar code paths, use `Agent(subagent_type="explore")` (or `AgentSwarm` for independent questions) instead of running many sequential searches yourself. Keep the results focused: restatement, file list, caller/callee map, and any `KNOWLEDGE.md` matches.

### Phase 2: Plan

For non-trivial tasks, call `EnterPlanMode` before writing the plan. The plan lives in `PLANNING.md` in the repository root, using this template:

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

Call `ExitPlanMode` to present the plan for approval. If any requirement is still ambiguous or multiple valid approaches remain, use `AskUserQuestion` first, then revise `PLANNING.md` before exiting.

MUST ask user: **"Here is my plan in PLANNING.md. Ready to proceed?"**

NEVER start implementation without explicit user approval.

### Phase 4: Implement

1. Mark the current step `in_progress` in `TodoList` and keep exactly one step in that state.
2. Make changes one logical unit at a time.
3. Update `DEVNOTES.md` if significant debugging or learning occurred.
4. Verify each unit against the validation gates below before moving to the next step.

### Phase 5: Cleanup

`PLANNING.md` is temporary local scratch state. Keep it current while working, but do not treat it as a branch/merge blocker because it is gitignored.

---

## Validation Gates

Every implementation slice must pass the relevant gates before you mark the task done:

1. **pytest** — run the focused band that covers the touched boundary, then the full suite if the change is broad.
2. **pyright** — for covered Python scope, keep type checks green.
3. **ROS build** — `colcon build --packages-select paint_interfaces paint_controller_ros2` when interfaces, `CMakeLists.txt`, or `package.xml` change.
4. **Offscreen startup/shutdown smoke** — run the touched smoke tests when QML contracts, shell behavior, or controller lifetime change.

### Test Harness Awareness

The test suite relies on a deliberately lightweight harness. Do not break these contracts:

- **Namespace-only stubs** — `tests/conftest.py` pre-registers `paint_controller` and several subpackages as empty `types.ModuleType` modules so tests can import submodules directly without triggering heavy `__init__.py` side effects. If you add new top-level re-exports in `__init__.py`, ensure they do not pull PySide6/ROS2 into pure-Python tests.
- **Force-assigned offscreen platform** — `os.environ["QT_QPA_PLATFORM"] = "offscreen"` in `tests/conftest.py` overrides any shell-level `xcb`. Never change this to `setdefault`.
- **`qt_core_app` is an alias of `qt_app`** — creating a second `QCoreApplication` aborts the suite. Tests needing only signal/QObject semantics should request `qt_core_app`, not create their own.
- **Teardown-specific regression coverage** — if your slice touches `QTimer`, worker pools, `QThread`, or controller `cleanup()`, add or update a teardown test (e.g. `tests/test_ssh.py` is the model) before closing the slice.
- **Startup-smoke contract parity** — if a slice changes a QML-facing contract, update the corresponding startup-smoke fixture in `tests/startup_smoke_support.py` so the smoke test exercises the new contract and does not silently fall back to a retired global.

---

## Stop and Ask Triggers

You MUST pause and ask for explicit guidance before:

- **Deleting any file**
- **Modifying launch files** (`launch/*.py`)
- **Changing ROS2 message types** or service definitions
- **Modifying CMakeLists.txt or package.xml**
- **Any change rated High complexity**

For ambiguous cases, use `AskUserQuestion` with concrete options. For stop-and-ask triggers that are clear-cut, state the blocker plainly and wait for direction.

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
2. **Check `KNOWLEDGE.md`** before debugging — solution may already exist
3. **Update `DEVNOTES.md`** after significant debugging sessions or feature work
4. **`INDEX.md` is the session-start map** — consult it in any fresh session before any other file
5. **Update `docs/tech-debt.md`** when new debt is discovered or existing items are resolved — move resolved items to the Resolved table with date and one-line note
