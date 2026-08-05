# Agent Instructions — Paint Controller

> **Start every session by reading `INDEX.md` first.** It gives orientation, the read-order checklist, and the authority hierarchy.

---

## Project Overview

ROS2 node with PySide6/QML UI for robotic paint controller on a Steam Deck. Python-first codebase; the historical C++ UI path has been removed from the live tree.

**Stack**: ROS2 (Humble/Jazzy), Python 3.10+, PySide6, QML

**Key Paths**:
- `python/paint_controller/` — Main Python application
- `python/paint_controller/qml/` — QML UI components
- `tests/` — pytest suite (offscreen Qt / fakes)
- This package has **no** in-tree `launch/` directory; do not invent launch files without an explicit user request

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

## Key design rule — Ousterhout × professional Qt

**Always follow the core of John Ousterhout's *A Philosophy of Software Design* without violating good design for a professional Qt (PySide6/QML) program.**

### Ousterhout core (what to optimize for)

Complexity is anything that makes software hard to understand or modify. Prefer designs that reduce:

1. **Change amplification** — one conceptual feature must not force edits across many unrelated homes
2. **Cognitive load** — a correct change should not require holding the whole graph in mind
3. **Unknown unknowns** — illegal or incomplete states should be hard to ship silently (deep ownership + integrity tests; not drift-by-default)

Prefer **deep modules**: small clear interfaces that **own real decisions** and hide implementation. Prefer **information hiding / co-located ownership** over pass-through layers, mega-façades, or multi-table hand-sync without a single owner.

Integrity tests are a **safety net for inevitable multi-representation boundaries** (QML↔Python strings, smoke fakes). They do **not** replace collapsing multi-home facts into one deep owner when that is possible in the same language/layer.

### Professional Qt (must not break)

For this product, professional Qt means:

- **QML** stays declarative and light on policy; layout/chrome only
- **Python** owns safety, hardware, ROS, persistence, legality, and machine-affecting behavior
- **`setContextProperty()`** composition bag — **no** mega-`Backend`, **no** `qmlRegisterSingletonInstance`
- Feature roots and overlays use **required property injection**; no ambient root-context reads inside shared stacks
- **Per-property NOTIFY** on status/settings (no blanket `changed` that storms bindings)
- **Discrete gated path** (`*Actions` + explicit `AdminActionGate.check_action`) stays separate from **continuous teleop** (`ControlProcessor` / engine — not under the gate)
- ROS callbacks do not freely mutate QObject properties off the UI thread (command bus / telemetry marshal)

Durable detail: `docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md` (“What Professional Qt Means Here”).

### Compatible “deep module” moves (do these)

- Co-locate form/action schemas with the owning Python module; QML binds list/map APIs
- `CONTEXT_PROPERTIES` as SOT for root names; limited smoke-fake generation for passthroughs
- Teleop catalog as SOT for menu/config/STANDARD apply; SPECIAL physics stay explicit code
- `ShellOverlayStack`-style shared composition with injected deps
- Shared mixins that keep safety calls **visible** (`GatedActionMixin._run_gated`)

### Rejected shortcuts (false Ousterhout / anti-Qt)

| Temptation | Why it fails |
|---|---|
| Mega-`Backend` / one god context object | Ambient coupling; fights feature roots and tests |
| Import-time self-registering controllers | Breaks typed factory graph, cleanup order, namespace-stub harness |
| Policy / legality / actuator math in QML | Moves safety into the declarative layer |
| Collapsing discrete admin + continuous teleop into one “Action” API | Wrong affinity (event vs ~60 Hz) and wrong safety model |
| Decorator magic that hides `@Slot` or the gate call | Breaks QML introspection and safety visibility |
| “Fewer files” by skipping factory / inject / smoke contracts | Correct Qt DI cost is not accidental spaghetti |

### When planning or reviewing

- Ask: *does this reduce change amplification / unknown unknowns for a real extension path (new toggle, command form, teleop mode, device family)?*
- Ask: *does it still look like professional Qt for this repo (inject, Python policy, no mega-Backend, dual control paths)?*
- If the two conflict, **keep professional Qt** and take the smaller depth win (co-located schema, integrity, thinner QML) rather than a façade that only renames ambient access.

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
**Ousterhout × Qt check**: [How this reduces change amplification / unknown unknowns without mega-Backend, policy-in-QML, or collapsing discrete vs continuous paths]
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

## TD-055 Layer Depth Review Bans (Problem 2)

When reviewing or implementing backend structure work, **reject**:

- New domain/policy rules under presentation-shaped `models/` (put plain policy in `handlers/policy/`)
- New QML-oriented `@Slot` growth on device `controllers/` (use `*Actions`)
- A second hardware HAL parallel to `ports/` (e.g. new ABCs under `services/workflow/hardware.py`)
- New `show_popup_fn` / peer-device orchestration dependencies on device controllers
- Pass-through-only types that do not hide a real decision (Ousterhout: prefer deep modules)

TD-055 Wave 1+2 is landed; residual only in `docs/tech-debt.md` (plan retired to git history).

---

## Stop and Ask Triggers

You MUST pause and ask for explicit guidance before:

- **Deleting any non-doc file** (code, config, tests). Deleting stale docs/plans/notes is routine per the Pruning Policy — no approval needed, but state what was deleted and why.
- **Adding or modifying ROS2 launch files** (none live in this package today; ask before creating them)
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

### Pruning Policy — judgment-based, git is the archive

DEVNOTES is an inbox of *current* context, and the same retention rule applies to all project docs (plans, boards, notes): **docs describe current reality.** Completed plans, superseded boards, and stale narratives are deleted, not archived — git history is the archive (`git log` / `git show` recover anything). Do not create verbatim cold-storage files such as `docs/devnotes/YYYY-QN.md`; the existing ones are frozen legacy.

**Prune trigger**: judgment, not a fixed calendar — e.g. DEVNOTES has grown past ~300 lines, an entry describes completed work whose details no longer affect current decisions, or a doc's statements no longer match the code.

**Prune steps** (per entry or doc):
1. Read it fully
2. Does it contain a reusable pattern, gotcha, anti-pattern, or design decision not yet in KNOWLEDGE.md or `docs/tech-debt.md`?
   - Yes → propose the extraction to the user for confirmation, then add it there
   - No → proceed to step 3
3. Delete it. Do not move it anywhere.

**What to extract → KNOWLEDGE.md**: gotchas, design decisions, anti-patterns, timing rules, discovered constraints

**What to delete freely**: step-by-step implementation narratives, file lists, "tried X failed" detail, completed plans, superseded boards

**What git handles** (do not duplicate anywhere): exact line changes, before/after code diffs, and all deleted history

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

1. **Ousterhout × professional Qt** — follow the Key design rule above on every structural change
2. **No standalone documentation files** unless user explicitly requests
3. **Check `KNOWLEDGE.md`** before debugging — solution may already exist
4. **Update `DEVNOTES.md`** after significant debugging sessions or feature work
5. **`INDEX.md` is the session-start map** — consult it in any fresh session before any other file
6. **Update `docs/tech-debt.md`** when new debt is discovered or existing items are resolved — move resolved items to the Resolved table with date and one-line note
