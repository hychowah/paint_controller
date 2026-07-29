# Layer Responsibility Depth Plan (Problem 2)

> Created: 2026-07-29  
> Updated: 2026-07-29 (Wave 2 — further depth after multi-section Ousterhout review)  
> Status: **Wave 1 (0–3) + Wave 2 (6–10) landed** on `td-055/layer-responsibility-depth` (2026-07-29). Phase 4′/5′ deferred (no empty rehome; status deepen only when consumer-driven).  
> Scope: Software layering and module depth — **not** UI/UX/HMI visuals, not a full safety program, not concurrency redesign as primary scope (see cross-links).  
> Authority: This file is the durable program plan for Problem 2.  
> Live board: `docs/plan/00_ARCHITECTURE_PROGRESS.md`  
> Debt IDs: **TD-055** (+ child slices TD-055.6 …) in `docs/tech-debt.md`  
> Design lens: John Ousterhout, *A Philosophy of Software Design* (deep modules, information hiding, different layer / different abstraction, pull complexity downward, strategic ~10–20% investment)

---

## 1. Problem statement

### 1.1 Name

**Problem 2 — Layers exist by folder, but responsibilities still mix.**

### 1.2 Original problem (why this program exists)

The package tree looks layered (`ports/`, `controllers/`, `handlers/`, `models/`, `services/`, `core/`). The **import graph is mostly acyclic**. The **responsibility graph was not**: dual HAL dialects, device controllers owning UI/orchestration, policy inside fat Qt types, open concrete/`Any` call sites.

### 1.3 Complexity (Ousterhout framing)

Complexity = anything that makes software hard to understand or modify.

| Cause | How it appears |
|---|---|
| **Change amplification** | Dual naming dialects; stringly `*Actions`; god factory bag |
| **Cognitive load** | Fat Teensy surface; `ControlProcessor` multi-role god module |
| **Unknown unknowns / obscurity** | Misleading package names; half-migrated patterns; dead pure helpers that *look* like SSoT |

### 1.4 Non-goals (entire program)

Do **not** treat as success criteria:

- Cosmetic folder renames without deeper modules
- Full Clean Architecture / empty presentation→application→domain shells
- Wide Protocol catalog that 1:1 mirrors every controller method
- Reopening TD-032 QML context name-retirement mega-program
- Mega-`Backend` or mega-session objects
- Industrial HMI / operator UX chrome
- TD-046 post-halt stick inhibit as primary deliverable (may couple later)
- TD-054 concurrent ROS publish+spin redesign (do not expand multi-thread publish)

---

## 2. Design principles (decision rules)

1. **Prefer deep modules** — simple interface, substantial implementation. Reject pass-through-only types.  
2. **Information hiding** — callers see capabilities, not hybrid ROS/Qt guts.  
3. **Different layer, different abstraction** — no pass-through “layers.”  
4. **Pull complexity downward** — ROS/Qt may stay *inside* adapters if outward surface is simple.  
5. **Collapse dual abstractions** — one hardware vocabulary; one verb language per path where practical.  
6. **Strategic investment (~10–20%)** — small slices that leave modules deeper.  
7. **Finish half-migrations** — if a pure helper or typed pattern exists, use it or delete it; do not leave dual truth.  
8. **Depth over rehome** — rename packages only after residual depth work lands.

**Hexagonal warning:** dependency arrows are a *result* of deep design, not the goal.

---

## 3. Wave 1 status (Phases 0–3) — landed 2026-07-29

### 3.1 What Wave 1 fixed

| Goal | Outcome |
|---|---|
| Dual ABC HAL | Removed `ITeensyController` / `IWinchController`; workflow adapters type against `ports/*` |
| Shared capability ports | `ports/winch.py`, `wheel.py`, `valve.py` + existing teensy/halt |
| Teensy foreign concerns | No `show_popup_fn` / peer winch / `demoAction` on controller |
| Multi-device demo | `handlers/demo_sequence.run_demo_action` |
| Pure legality | `handlers/policy/action_legality.py`; thin `AdminActionGate` |
| Teleop map extract | `handlers/policy/teleop_control_map.py` (table builder) |
| Hurt call sites | `ControlProcessor` device deps → ports; `WheelActions` / `WinchActions` → invoke lambdas |
| Process | Review bans in `AGENTS.md`; package honesty notes |

**Evidence:** branch `td-055/layer-responsibility-depth`, tests `tests/test_layer_responsibility_depth.py`, full suite green at land.

### 3.2 Multi-section Ousterhout residual (why Wave 2 exists)

Independent section scores after Wave 1 (~6.3 overall):

| Section | Score | Residual (Wave 2 targets) |
|---|:---:|---|
| Ports / dual HAL | 7 | Identity Protocols; workflow rename dialect; dual getattr; double availability guards |
| Device adapters | 6 | Teensy still shallow/topic-shaped public surface; presentation helpers on device |
| Pure policy | 6.5 | Legality strong; teleop map incomplete; **`scale_joystick_axis` unused in production** |
| Presentation Actions | 6.5 | Wheel/Winch deep; **Teensy/Tuning/Recording/System still stringly** |
| ControlProcessor | 5 | **God module**; helpers temporal; port gap on wheel travel |
| Composition / packages | 6.5 | Fat factory/`ControllerBundle`; shell vs actions split; name lies |

### 3.3 Why Wave 1 did not fix these (intentional)

- Success bar was Phases 0–3 metrics, not “every section 9/10.”  
- Ousterhout rewrite forbade full port catalogs and retype-everything as early work.  
- “Hurt call sites only” left other `*Actions` residual by design.  
- God-object CP split and Teensy surface redesign are larger than dual-HAL collapse.  
- Incomplete teleop extract (dead scaler) is a **finish-the-migration** item, not a new theme.

---

## 4. Target shape (unchanged north star)

```text
QML
  → presentation   (*Status, *Actions, shell façades)     [Qt OK; no ROS; no multi-device demos]
       → application  (teleop policy, legality, safety, workflow ops, demo)
            → hardware capability interfaces (few, deep)   [no Qt, no ROS]
                 → adapters/controllers                    [ROS/Qt inside; no UI callbacks; no peer orchestration]
Composition root wires once; does not own presentation bulk or business rules.
```

| Role | May own | Must not own |
|---|---|---|
| Device adapter | Pubs/subs, availability, status, port methods | Popup, peer orchestration, demo sequences, formatting for UI |
| Capability port | Coherent clusters with ≥2 consumers | One-method identity Protocols for show |
| Application / policy | Legality, teleop engine/map, halt coord, demo | ROS msg types; fat QML property trees |
| Presentation | CamelCase read models, gated slots | Domain tables; multi-device demos |
| Composition root | Construct + wire + shutdown | Growing business rules |

---

## 5. Wave 1 phases (historical — complete)

### Phase 0 — Stop the bleeding ✅

Review bans, honesty notes, TD-055 board registration.

### Phase 1 — Collapse dual HAL ✅

Inventory, shared ports, thin workflow adapters, no competing ABC HAL.

### Phase 2 — Peel Teensy foreign concerns ✅

No popup/peer on Teensy; `demo_sequence`; ban new QML `@Slot` on controllers.

### Phase 3 — Pure policy + hurt retypes ✅ (partial teleop depth)

Legality pure; map builder pure; CP + Wheel/Winch Actions retyped.  
**Known incomplete:** production does not use `scale_joystick_axis`; CP still owns real teleop complexity.

---

## 6. Wave 2 — further Problem 2 depth (active)

Canonical order is **depth-first**. Do **not** start with Phase 5-style renames or Phase 9 package moves.

```text
Phase 6  Finish half-migrations (scaler, dual getattr, port honesty)     [quick depth wins]
   ↓
Phase 7  Presentation Actions migration (Teensy → Tuning → others)      [finish family pattern]
   ↓
Phase 8  Continuous teleop engine depth (ControlProcessor)              [largest cognitive load]
   ↓
Phase 9  Device surface deepen (Teensy public API) + naming dialect     [interface depth]
   ↓
Phase 10 Composition depth (subsystem builders, narrow wiring ports)    [graph edge]
   ↓
Phase 4′ Status deepen (opportunistic)   [was Phase 4; still optional]
   ↓
Phase 5′ Light rehome / name honesty     [was Phase 5; last]
```

### Phase 6 — Finish half-migrations (P0 for Wave 2)

**Goal:** Eliminate dual truth introduced or left by Wave 1. Ousterhout: a pure helper that only tests call is worse than no helper.

| ID | Work | Done when |
|---|---|---|
| 6.1 | **Use or delete `scale_joystick_axis`** — rewire `_process_standard_control` and `winch_teleop` (and any matching clamp paths) **or** remove from public policy API | Single production scaling path; no orphan pure helper |
| 6.2 | **ManualCommandHandler winch** — call `move_increment_with_accel` only; remove `moveIncrementWithAccel` getattr fallback | One verb; port contract trusted |
| 6.3 | **WinchActions state reads** — use protocol properties (`enabled`, etc.) instead of `_winch_echo(attribute_string)` where declared | No string attribute discovery on typed ports |
| 6.4 | **Wheel teleop port honesty** — extend `SupportsWheelTeleop` (or add a small sibling port) with `command_position` used by travel fire; type `wheel_travel_teleop` against it | Port matches what Continuous teleop actually calls |
| 6.5 | **Collapse identity noise** — `SupportsValveCommand` as alias of halt **or** one name only for safety+teleop | No inheritance ladder for the same method |
| 6.6 | **Double availability** — pick one layer (adapter **or** action handler) to own “missing hardware”; document the other | No permanent dual guards without comment |

**Anti-goals:** New packages; expanding Protocol count for completeness.

**Validation:**

- `tests/test_layer_responsibility_depth.py`, control_processor, winch_teleop, manual_commands, wheel actions  
- Grep: no production-unused `scale_joystick_axis` **or** proven call sites from CP/helpers  
- Full suite before closing phase  

**Complexity reduced:** obscurity (dual truth), change amplification (one winch verb).

---

### Phase 7 — Finish presentation Actions pattern

**Goal:** One family design. “An `*Actions` class” must mean typed invoke, not half stringly.

| ID | Work | Done when |
|---|---|---|
| 7.1 | **TeensyActions** → Wheel-style `invoke` lambdas; small Protocol (or extend ports) only for methods called | No `method_name` + `getattr` in this module |
| 7.2 | **TuningActions** → same (two PID APIs; free win) | No string method dispatch |
| 7.3 | **RecordingActions** / **SystemActions** (and BaseTopView if still stringly) when touched | Same pattern; no shared abstract `method_name` runner |
| 7.4 | **ManualCommandHandler identity** — stable command ids (`spray_gun_angle`, …); QML holds display labels | Rename of combo text does not break dispatch |
| 7.5 | Keep domain depth: Teensy intent-vs-status toggles; Tuning QML names hiding firmware-ish APIs | Behavior parity; only binding mechanism changes |

**Anti-goals:**

- Shared `BaseActions` that still takes `method_name: str` (entenches anti-pattern)  
- Merging all Actions into one mega-object  

**Validation:**

- Existing `*Actions` tests + manual command tests + startup smokes if QML keys change  
- Structural test: no `method_name=` in migrated modules  

**Complexity reduced:** cognitive load (consistent family), change amplification (renames type-checkable).

---

### Phase 8 — Continuous teleop engine depth

**Goal:** `ControlProcessor` stops being a god module. Qt façade thin; one deep engine owns continuous motion.

| ID | Work | Done when |
|---|---|---|
| 8.1 | Extract **`ContinuousTeleopEngine`** (same file or one sibling module — **not** a micro-file forest) with `tick(input, modes) -> DisplaySnapshot` | Non-Qt logic unit-testable without QObject |
| 8.2 | `ControlProcessor` becomes: call engine, set properties / `display_message`, settings → `engine.apply_limits` | Clear façade vs engine boundary |
| 8.3 | **Deepen control map** (pick A or B, not both half-done): **A)** map rows carry enough to drive standard/trigger paths (axis, cast, actuator binding at setup); **B)** honest static templates only + engine owns dynamics — document which | Adding a simple mode is one table/row change, not a new method + display branch + dispatch entry |
| 8.4 | Helpers return values (winch tick result, travel mm) — **do not** mutate HUD `current_values` inside helpers | Display assembly centralized once |
| 8.5 | Heartbeat lock for winch: Protocol or `Callable[[], bool]` — no `Any` handler in winch helper | Port discipline through helpers |
| 8.6 | Optional later: post-halt stick inhibit (TD-046) as engine policy flag — **only** if product prioritizes; not required to close Phase 8 | Documented if deferred |

**Anti-goals:** One file per mode; second teleop framework; expanding multi-thread publish (TD-054).

**Validation:**

- Full control_processor / winch_teleop / wheel_travel / input / safety integration bands  
- Full suite required (blast radius high)  
- Behavior parity: rates, deadzones, winch activation, travel A-button, track curve, yaw offset semantics  

**Complexity reduced:** cognitive load (god object), information hiding (engine interface).

---

### Phase 9 — Device surface + naming dialect

**Goal:** Device modules are deep at the *boundary*, not only inside. One verb language where dual dialect remains.

| ID | Work | Done when |
|---|---|---|
| 9.1 | **Teensy:** ban new `@Slot`; cluster public API by capability ports; delete/implement dead paths (e.g. unused yaw pub paths) | No dead public methods; Slot growth frozen |
| 9.2 | Move presentation helpers off Teensy (`get_formatted_value` → status projection or *Status) | Device does not format for UI |
| 9.3 | Prefer Winch-style domain methods + thin aliases over Slot-only topic API (incremental, not big-bang rewrite) | At least one high-churn cluster deepened |
| 9.4 | **Workflow naming dialect:** adapters keep **port/controller method names** *or* explicit workflow Protocol in `ports/` — pick one; update action handlers | One rename path for a hardware method |
| 9.5 | Opportunistic: peel `show_popup_fn` from non-device constructors only when touching SSH/bag (prefer result/error ports) | Factory no longer normalizes popup on every leaf |

**Anti-goals:** Second HAL under `services/`; mega Teensy rewrite in one PR.

**Validation:** teensy tests, workflow scheduler/executor, manual commands, factory.

---

### Phase 10 — Composition depth (graph edge)

**Goal:** Composition root stays orchestration; factory is deep subsystem builders, not one flat god procedure.

| ID | Work | Done when |
|---|---|---|
| 10.1 | Split `create_controllers` into 3–4 builders (e.g. devices, control plane, presentation actions, workflow/services) composed by one thin function | Adding a wheel action touches one builder |
| 10.2 | Narrow wiring: stop passing whole `ControllerBundle` into SignalWiring/composer where possible — small frozen ports of used fields | Bundle remains private cleanup product if needed |
| 10.3 | Type factory inputs (reduce `Any` / drop `cast(Any, HardwareControllers)` if possible) | Composition root is most honest, not least |
| 10.4 | Document decision rule: new QObject → factory field vs AppRuntime field | No shell vs actions split without rule |

**Anti-goals:** DI container framework; empty package taxonomy; big-bang `ControllerBundle` rename without interface narrowing.

**Validation:** factory + AppRuntime + signal_wiring + qml_context_composer + startup smoke bands.

---

### Phase 4′ — Status deepen (optional; was Phase 4)

Unchanged intent: status as deep read model; fail-loud wiring on touched façades; no new context keys without retirement.

Schedule **after** Phase 7–8 unless a consumer forces status work earlier.

### Phase 5′ — Light rehome (optional; last)

Only after Wave 2 depth metrics improve:

- Optional `presentation/` rehome of `*Status`/`*Actions`  
- Composer façades labeled presentation  
- No empty hexagon folders  

---

## 7. Execution order (full program)

```text
WAVE 1 (landed)
  0 bans → 1 dual-HAL → 2 Teensy peel → 3 pure policy + hurt retypes

WAVE 2 (active)
  6 half-migrations → 7 Actions family → 8 teleop engine → 9 device/dialect → 10 composition
  → 4′ status (optional) → 5′ rehome (last)
```

**Hard rules:**

- Do **not** open Phase 5′ renames before Phases 6–8.  
- Do **not** invent pass-through-only types for architecture.  
- Do **not** retype unused devices “for completeness.”  
- Prefer **one vertical slice** per PR with the §8 checklist.

---

## 8. Slice template (every PR)

```markdown
### TD-055.x — [title]

**Phase**: 6–10 | 4′ | 5′
**Complexity reduced** (pick ≥1):
- [ ] Change amplification
- [ ] Cognitive load
- [ ] Obscurity / dual truth finished

**Depth check**:
- [ ] Simpler outward interface or removed dual path
- [ ] No pass-through-only type
- [ ] No second HAL / popup-on-device / peer-on-device
- [ ] No new pure helper without a production caller

**Files**: …
**Validation**: pytest …
**QML contract**: frozen / delta …
**Rollback**: revert PR
```

---

## 9. Call-cluster inventory (living)

| Consumer | Coupling after Wave 1 | Wave 2 target |
|---|---|---|
| `ControlProcessor` | Ports typed; still god object | Engine + façade; honest wheel port; pure scaler used or gone |
| `WheelActions` / `WinchActions` | Typed invoke | Keep; minor property-read cleanup |
| `TeensyActions` / `TuningActions` | Stringly residual | Typed invoke (Phase 7) |
| `RecordingActions` / `SystemActions` | Stringly residual | Typed when touched (Phase 7) |
| `ManualCommandHandler` | Ports + demo_sequence; dual winch getattr; UI-label keys | One winch verb; stable ids (6 + 7) |
| Workflow adapters | Ports; snake rename dialect | One dialect (Phase 9) |
| Safety | Halt ports | Unchanged unless halt set expands elsewhere |
| Factory / wiring | Fat bag | Subsystem builders + narrow ports (Phase 10) |

---

## 10. Validation gates (program-wide)

1. Focused pytest for touched modules.  
2. Full suite when blast radius ≥ factory + teleop + multiple Actions (Phase 8 always).  
3. pyright on touched Python scope.  
4. Startup smoke only if QML contracts change.  
5. No new context property without last-consumer retirement.  
6. Teardown tests if timers/threads/cleanup change.  
7. **Structural tests** for Wave 2: no orphan `scale_joystick_axis`; no `method_name=` in migrated Actions; port source contains methods continuous teleop calls.

---

## 11. Success metrics

### Wave 1 (met)

| Metric | Status |
|---|---|
| One primary ports vocabulary for Teensy/Winch/wheel/valve clusters | ✅ |
| Teensy without popup/peer/demo | ✅ |
| Legality pure-testable | ✅ |
| CP + Wheel/Winch free of open string method dispatch | ✅ |
| No second ABC HAL | ✅ |

### Wave 2 (active bar — “done enough” for further Problem 2 improvement)

| Metric | Target |
|---|---|
| No dual-truth pure helpers | Scaler used in production **or** deleted |
| Actions family consistency | Teensy + Tuning (min) use invoke pattern; no new stringly Actions |
| Teleop module depth | CP is thin Qt shell **or** engine extraction landed with one public `tick`/`process` and tests without full QObject for core math |
| Port honesty | Continuous teleop ports declare all methods used on the hot path |
| One winch motion verb on manual/workflow paths | No dual getattr names |
| Composition | Factory not a single 190-line flat script **or** wiring no longer requires whole-bag ports for new signal hooks |
| Shallow types | Net zero new pass-through-only façades |

Optional stretch: package rehome (Phase 5′); Teensy surface fully Winch-like.

---

## 12. Cross-links (out of primary scope)

| Topic | Where | Relation |
|---|---|---|
| QML context freeze | TD-032 / TD-047 / board | Preserve |
| Post-halt teleop inhibit | TD-046 residual | May land inside Phase 8.6 if prioritized |
| ROS concurrent I/O | TD-054 | Separate; do not expand multi-thread publish |
| Legality field defaults | product/settings | Not Wave 2 depth metric |
| Durable Qt architecture | `01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md` | Product north star |

---

## 13. Rollback philosophy

- Prefer forward fixes within a phase.  
- Each slice independently revertable.  
- Dual dialect merges: temporary shims deleted in same phase.  
- Never leave two permanent hardware vocabularies without quarantine note + retirement in this file.

---

## 14. Next slice recommendation (implement when approved)

**Start Wave 2 with Phase 6 (half-migrations)** in one or two tight PRs:

1. **6.1 + 6.4 + 6.2** together if small: scaler use-or-delete, wheel port honesty, manual winch single verb.  
2. Then **Phase 7.1–7.2** (TeensyActions + TuningActions → invoke).  
3. Only then open **Phase 8** teleop engine (largest, needs full suite).

**Do not** start with Phase 5′ renames or a Teensy mega-rewrite.

---

## 15. Preserve list (do not “fix away”)

- `AppRuntime` staged composition + compose/wiring ports  
- Leaf controllers (no upward imports)  
- `ports/` as single capability vocabulary  
- `demo_sequence` multi-device ownership  
- Pure `evaluate_action_legality` + thin gate  
- Wheel/Winch Actions invoke pattern (reference)  
- Continuous vs discrete teleop split  
- Bundle cleanup order + leftover detection  
- Review bans in `AGENTS.md`  

---

## 16. Document history

| Date | Change |
|---|---|
| 2026-07-29 | Initial plan (Ousterhout critique of early improvement steps) |
| 2026-07-29 | Wave 1 Phases 0–3 landed (inventory §8, TD-055 status) |
| 2026-07-29 | **Wave 2 added**: multi-section Ousterhout residual; Phases 6–10 active order; Wave 1 closed as historical; next slice = Phase 6 half-migrations |
