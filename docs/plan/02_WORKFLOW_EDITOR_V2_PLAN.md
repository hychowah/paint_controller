# Workflow Editor v2 — Master Plan

**Status**: Implementation in progress  
**Branch**: `feature/workflow-editor-v2` (from `dev`)  
**Complexity**: High  

Related: `ARCHITECTURE.md`, `docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md`, `services/workflow/*`.

---

## 1. Goal

Steam Deck **touch-first full-page** workflow programming:

- Open from **System Control → WorkFlow → Edit** (not a System Control tab).
- Build/edit sequences without keyboard/mouse: palette add, step list, numpad params, save.
- Teach-pendant style: move winch, concurrent spray + angle, wait, move, loop/end.
- **Rewrite** document + editor session (no dual-model debt).
- v1 UI is simple; document/compile **reserves advanced timing** for later without rewrite.

---

## 2. Product decisions (locked)

| Topic | Decision |
|---|---|
| Surface | **Full-page overlay** from WorkFlow → **Edit**; close system control when editor opens |
| Branch | `feature/workflow-editor-v2` |
| v1 authoring model | **Simple**: linear steps + parallel groups + wait + continue policy + document loop |
| Advanced timing | **Not in v1 UI**, but **first-class extension points** in document/compile; preserve-on-edit |
| Old Edit WorkFlow tab | **Retire** after cutover |
| On-disk format | Single `schema_version: 2` SOT |

### Explicit non-goals (v1)

- Freeform trigger-graph / position-trigger authoring UI  
- Behavior-tree / node-graph editor  
- SelectBar permanent page route for the editor  
- Editing while workflow is running/paused  

---

## 3. Operator model (v1)

### Entry / exit

1. System Control → WorkFlow.  
2. **Edit** → opens Workflow Editor full-page overlay.  
3. System Control closes when editor opens.  
4. **Back** closes editor; dirty → save/discard (Python-owned).

### Step vocabulary

| Kind | Meaning |
|---|---|
| `action` | One device command (winch, valve, gimbal, arm, force) |
| `wait` | Pure time delay |
| `parallel` | Several actions **start together** |
| document `loop` | After last step, restart at step 1 or end |

### Continue policy

- `wait_complete` — next step after this step’s completion window  
- `continue_immediately` — fire and proceed (schedule overlap allowed)

---

## 4. Document model (`schema_version: 2`)

```yaml
schema_version: 2
name: spray_cycle
description: ...
loop: true
steps:
  - id: step_01
    kind: action
    type: winch_absolute
    params: { length: 2360, speed: 250, acceleration: 10 }
    continue: wait_complete
    # timing: {}   # reserved for advanced timing

  - id: step_02
    kind: parallel
    continue: wait_complete
    members:
      - id: m1
        type: valve_turn
        params: { turn_value: 3.0 }
        # timing: { mode: before_complete, offset_ms: 500, ... }  # v1.1+
      - id: m2
        type: spray_gimbal
        params: { angle: 12.0, speed: 10.0 }

  - id: step_03
    kind: wait
    duration_ms: 1000
```

### Extension points (structure now; UI later)

| Extension | Purpose |
|---|---|
| `member.timing` / `step.timing` | mid-motion closes, delayed starts |
| `at_position` mode | position-crossing triggers |
| `group_wait` | max_duration (v1 default) vs primary |

**Preserve-on-edit**: advanced `timing` blocks must not be stripped on param-only saves.

### Compile (v1)

- `wait` → advance timeline by duration  
- `action` + `wait_complete` → schedule, then advance by duration  
- `action` + `continue_immediately` → schedule, do not advance by duration  
- `parallel` → all members same start time; advance by max duration when wait_complete  

---

## 5. Backend package shape

```
services/workflow/
  document.py            # pure WorkflowDocument / steps
  document_migrate.py    # legacy actions[] → v2
  document_compile.py    # v2 → schedule actions for executor
  workflow_editor.py     # session owner (QObject)
  workflow_runner.py     # load/compile/collision
  workflow_executor.py   # run schedule + time_wait
  action_schema.py       # types + palette + time_wait
```

Python owns mutations, dirty, validation, save/load. QML binds and calls slots only.

---

## 6. Shell / QML

- `OverlayHostPolicy.workflow_editor_active`  
- Full-page `features/workflow/WorkflowEditorWorkspace.qml`  
- Inject `workflowEditor` via system control services / required properties  
- WorkFlow tab **Edit** button; retire System Control “Edit WorkFlow” tab  

---

## 7. Phases

1. Document + migrate + compile + pure tests  
2. Editor session rewrite + unit tests  
3. Runner/executor v2 + time_wait + sample YAML  
4. Full-page QML + overlay + retire old tab  
5. Focused pytest green  

---

## 8. Ousterhout × professional Qt

Deep document/compile/session modules; no mega-Backend; inject feature root; no policy in QML; teleop/gate paths untouched.
