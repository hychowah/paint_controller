# Layer Responsibility Depth Plan (Problem 2)

> Created: 2026-07-29  
> Status: **Phases 0–3 landed** on branch `td-055/layer-responsibility-depth` (2026-07-29). Phases 4–5 optional.  
> Scope: Software layering and module depth — **not** UI/UX/HMI visuals, not a full safety program, not concurrency redesign as primary scope (see cross-links).  
> Authority: This file is the durable program plan for Problem 2.  
> Live board: `docs/plan/00_ARCHITECTURE_PROGRESS.md`  
> Debt IDs: register slices under **TD-055** (and children) in `docs/tech-debt.md`  
> Design lens: John Ousterhout, *A Philosophy of Software Design* (deep modules, information hiding, different layer / different abstraction, pull complexity downward, strategic ~10–20% investment)

---

## 1. Problem statement

### 1.1 Name

**Problem 2 — Layers exist by folder, but responsibilities still mix.**

### 1.2 What is wrong

The package tree looks layered (`ports/`, `controllers/`, `handlers/`, `models/`, `services/`, `core/`). The **import graph is mostly acyclic** (controllers stay leaves). That is necessary but not sufficient.

The **responsibility graph is not layered**:

| Folder | Name suggests | What many types actually do |
|---|---|---|
| `ports/` | Single hardware boundary | Thin seed (halt + partial Teensy); incomplete |
| `controllers/` | Device I/O adapters | ROS + Qt `QObject` hybrids; some hold UI callbacks and peer devices |
| `handlers/` | Application services | Policy + Qt (+ sometimes ROS/UI strings); quality uneven |
| `models/` | Domain models | Mostly QML presentation (`*Status` / `*Actions`) + some policy as `QObject` |
| `services/workflow/` | Workflow use cases | Contains a **second** hardware HAL (`hardware.py` ABCs/adapters) |
| `core/` | Composition + shared platform | Composition root **and** large QML façade factory (`qml_context_composer`) |

### 1.3 Complexity (Ousterhout framing)

Complexity = anything that makes software hard to understand or modify. This problem shows all three causes:

| Cause | How it appears here |
|---|---|
| **Change amplification** | Dual HAL; device class owns popup + demo + peer winch; stringly `*Actions` + concrete teleop types |
| **Cognitive load** | One type = ROS + Qt + policy + presentation + orchestration |
| **Unknown unknowns / obscurity** | Misleading names (`models/`); “which hardware interface is real?”; unclear who may call whom |

Acyclic imports only prove **no cycles**. They do not prove **deep modules** or **different abstractions per layer**.

### 1.4 Non-goals for this program

Do **not** treat as success criteria for this plan:

- Cosmetic folder renames without deeper modules
- Full Clean Architecture / hexagonal purity for its own sake
- Empty `presentation/` → `application/` → `domain/` shells
- Expanding a large Protocol catalog that 1:1 mirrors controller methods (wide **shallow** ports)
- Reopening TD-032 QML name-retirement mega-program
- Mega-`Backend` or mega-session objects
- Industrial HMI / operator UX chrome work
- Full post-halt teleop inhibit / legality field defaults (related residual elsewhere; not the primary goal here)
- TD-054 ROS publish+spin ownership (cross-link only; do not block this program, do not expand multi-thread publish while touching teleop)

---

## 2. Design principles that govern this plan

From *A Philosophy of Software Design*, applied as decision rules:

1. **Prefer deep modules** — simple interface, substantial implementation. Reject types that only pass through.
2. **Information hiding** — hide decisions likely to change (ROS/Qt bridging, device details). Callers see capabilities, not hybrid objects.
3. **Different layer, different abstraction** — if two “layers” expose the same concepts via pass-through methods, they are not layers.
4. **Pull complexity downward** — ROS/Qt mess may stay **inside** adapters for a long time; that is fine if outward interfaces stay simple.
5. **Collapse dual abstractions** — one hardware vocabulary, not `ports/` + workflow HAL + `Any` method names.
6. **Strategic investment (~10–20%)** — small slices that leave modules deeper; no purity rewrite.
7. **Stop new lies immediately** — review bans before large restructure.
8. **Names are interfaces** — rename when names still lie *after* depth improves; ban new domain under presentation-shaped packages now.

**Hexagonal warning:** dependency arrows are a *result* of deep design, not the goal. Ports are tools for depth, not a completeness badge.

---

## 3. Target shape (north star for Problem 2)

Fewer, **deeper** modules. Same process; clearer ownership of ideas.

```text
QML
  → presentation   (*Status, *Actions, shell façades)     [Qt OK; no ROS; no multi-device demos]
       → application  (teleop policy, legality, safety orchestration, workflow ops)
            → hardware capability interfaces (few, deep)   [no Qt, no ROS]
                 → adapters/controllers                    [ROS/Qt may live INSIDE; no UI callbacks; no peer orchestration]
Composition root wires once; does not own presentation bulk or business rules.
```

### 3.1 Role rules (acceptance of “honest layers”)

| Role | May own | Must not own |
|---|---|---|
| **Device adapter (controller)** | Pubs/subs, availability, device status, methods that implement capability interfaces | `show_popup_fn`, peer-device orchestration, new QML `@Slot` surface growth, demo sequences |
| **Hardware capability interface** | Coherent command/status/halt clusters used by ≥2 consumers | One-method Protocols invented only for typing purity |
| **Application / policy** | Legality tables, teleop mapping, halt coordination, workflow sequences | ROS msg types, QML property trees (thin shells OK) |
| **Presentation** | CamelCase read models, gated action slots for QML | Domain tables, ROS, multi-device demos |
| **Composition root** | Construct + wire + shutdown order | Growing private façade classes / business rules |

### 3.2 What “few deep ports” means

Not one Protocol per controller method. Prefer **capability clusters** drawn from **real call sites**:

| Candidate deep surface (illustrative) | Hides | Callers today |
|---|---|---|
| **Halt / inert set** | Per-device zero/stop details | `SafetyCoordinator`, emergency, heartbeat loss |
| **Teensy continuous motion** | Prop/rail/spray stick surface | `ControlProcessor` |
| **Teensy body / workflow motion** | Arm, pitch, force, etc. | workflow adapters |
| **Winch motion + halt** | speed / absolute / status read as needed | teleop, actions, safety, workflow |
| **Wheel motion + halt** | speed / e-stop / status | teleop, actions, safety |
| **Valve command + halt** | turn setpoints | teleop, safety, workflow |
| **Operator notify** (optional, small) | popup/toast channel | Actions / application — **not** controllers |

Add a surface only when it **hides a real decision** or unifies two call paths. Do not invent ports “for completeness.”

Controllers may remain ROS+Qt hybrids **internally** for a long time. Complexity is pulled **downward** into the adapter.

---

## 4. Current evidence anchors (code, not aspirational docs)

Use these as starting points; re-verify in each slice:

| Symptom | Evidence |
|---|---|
| Controller owns UI + peer device | `TeensyController(..., winch_controller=..., show_popup_fn=...)`; `demoAction` drives winch |
| Dual HAL | `ports/teensy.py` + `services/workflow/hardware.py` ABCs/adapters |
| Partial ports | `ControlProcessor` types concrete wheel/winch/valve; Teensy via `SupportsTeensyTeleop` only |
| Stringly / duck actions | `*Actions` take `Any`, call by `method_name` |
| Presentation misnamed domain | `models/*Status`, `*Actions`; `AdminActionGate` is policy-as-`QObject` |
| Façades in “core” | `core/qml_context_composer.py` large private façade set |
| Better patterns already present | `SafetyCoordinator` + halt Protocols; `WheelStatus` projections; factory DI; TD-049 Teensy port seed |

---

## 5. Program phases

Each phase is a **bounded slice family**. Land one vertical win per PR when possible. Every phase must leave **deeper modules** or **less change amplification**, not just new files.

### Phase 0 — Stop the bleeding (review bans + honesty)

**Goal:** Prevent new mixed responsibilities while the program runs.

| ID | Work | Done when |
|---|---|---|
| 0.1 | **Review bans** (PR checklist / short note in this plan + AGENTS or tech-debt pointer) | Reviewers reject: new domain/policy under presentation-shaped `models/`; new QML `@Slot` on device controllers; new second HAL path; new `show_popup_fn` / peer-device deps on controllers |
| 0.2 | **Honesty note** (this section + optional one-line package comments only if helpful) | `models/`, `ports/`, `core/` actual roles stated; no large rename |
| 0.3 | Register **TD-055** program + child slice IDs in `docs/tech-debt.md`; link from `00_ARCHITECTURE_PROGRESS.md` | Board points here as active software program for Problem 2 |

**Anti-goals:** Mass package rename; empty layer folders.

**Validation:** Docs-only / process; no behavior change required.

---

### Phase 1 — Collapse dual HAL into one deep hardware vocabulary

**Goal:** One place defines hardware capabilities. Workflow stops being a parallel dialect.

| ID | Work | Done when |
|---|---|---|
| 1.1 | Inventory call clusters: teleop, `*Actions`, safety halt, workflow adapters, manual commands | Written inventory table in this plan §8 (update in-slice) |
| 1.2 | Merge workflow Teensy/Winch ABCs into the shared port home **by use** (extend `ports/` or equivalent) | Workflow adapters implement / wrap the **same** surfaces; no competing ABC definitions for the same capability |
| 1.3 | Prefer **few** Protocols/capability types over method-for-method mirrors | Each new port has ≥2 real consumers or unifies two paths; shallow 1-method ports rejected in review |
| 1.4 | Delete or thin dead workflow ABC surface after adapters move | Single import path for “what workflow needs from Teensy/Winch” |

**Pull complexity downward:** Adapters may still wrap concrete controllers. Do not require pure non-Qt controllers in this phase.

**Validation:**

- Workflow + existing port consumers still green (`tests/test_workflow_*`, `tests/test_safety_*`, teleop-related)
- No new dual interface for the same method cluster
- Factory still sole constructor of concrete controllers

**Cross-link:** Complements TD-049 (Teensy seed). Does not require TD-054.

---

### Phase 2 — Peel foreign concerns off the worst device adapters

**Goal:** Controllers are devices. UI and multi-device orchestration leave the adapter.

| ID | Work | Done when |
|---|---|---|
| 2.1 | Remove `show_popup_fn` from `TeensyController` (and any similar device-owned popup deps found) | Controllers do not import/call presentation; toasts live in `*Actions` or a small notify capability used by application/presentation |
| 2.2 | Remove `winch_controller` from `TeensyController` | No peer device field on Teensy |
| 2.3 | Relocate `demoAction` to application/workflow as **one deep operation** (“run demo” hides sequencing) | Single entrypoint; not a forest of pass-through services |
| 2.4 | Ban enforced: no **new** `@Slot` on controllers for QML; new QML entry points only on `*Actions` | Grep/review gate; existing slots may remain as plain methods until callers migrate (optional later) |

**Depth check:** If a new type only forwards one call, do not add it — put the call on the existing Actions/workflow owner.

**Validation:**

- Focused teensy / factory / actions tests green
- Startup smokes unchanged unless a QML-facing contract moves (prefer no contract change)
- Demo/popup behavior parity (manual or existing tests)

---

### Phase 3 — Deepen policy modules (pull rules out of fat Qt shells)

**Goal:** Policy has a simple interface; Qt shells stay thin.

| ID | Work | Done when |
|---|---|---|
| 3.1 | Extract `AdminActionGate` evaluation tables/logic to plain Python with a small API (e.g. evaluate / check) | Core rules unit-testable without QObject semantics; thin `QObject` wrapper remains for QML if needed |
| 3.2 | Extract ControlProcessor teleop **maps** (mode → scale/interval/command resolution) to plain modules | Processor becomes: read input → resolve commands → call capability interfaces; display properties may stay on a thin shell |
| 3.3 | Retype the **call sites that hurt** (`ControlProcessor`, primary `*Actions`, ManualCommandHandler where touched) against the **few** ports from Phase 1 | Kill `Any` + method-name strings at those sites; do **not** retype the entire tree “for purity” |

**Anti-goals:** Policy “framework”; micro-files that re-export the same rules.

**Validation:**

- Existing gate / control_processor / actions tests updated and green
- No behavior change except intentional parity fixes recorded in DEVNOTES

**Cross-link residual:** Post-halt stick inhibit (TD-046 residual) may touch `ControlProcessor` later; do not block Phase 3 pure extract on that feature unless the slice explicitly includes it.

---

### Phase 4 — Status as a deep read model (not pass-through)

**Goal:** Presentation reads stable status abstractions; does not scrape hybrid controllers as the long-term story.

| ID | Work | Done when |
|---|---|---|
| 4.1 | Where dual scrape paths remain, feed `*Status` from stable snapshots or port-level status reads | Adding a telemetry field has one producer contract |
| 4.2 | Resist Status-as-pass-through: prefer answering operator questions with low cognitive load (existing per-property NOTIFY pattern is good — keep deepening that, not wrapping twice) | No new Status layer that only renames controller fields without a consumer win |
| 4.3 | Opportunistic: reduce duck-typed `_read_object_value` / silent `_connect_if_signal` in composer for **touched** façades toward fail-loud wiring (parity with status models) | Touched façades only; no mega-composer rewrite |

**Validation:** Status model tests + startup smokes for touched families.

**Anti-goals:** New app-scope context keys; reopening frozen shell contracts without need.

---

### Phase 5 — Composition hygiene and light rehome

**Goal:** Composition root wires; names stop lying. **Only after** Phases 1–3 have real depth gains.

| ID | Work | Done when |
|---|---|---|
| 5.1 | Keep `AppRuntime` as composition root; move façade construction bulk out of overloaded “core means everything” if still painful (e.g. `presentation/` or keep composer but document as presentation) | `core/` meaning = runtime platform + wiring, not growing private UI façades without label |
| 5.2 | Optional package rehome of pure presentation (`*Status`/`*Actions`) **only if** names still confuse after depth work | Import updates + tests green; no behavior change |
| 5.3 | Optional: group plain policy under a small `application/` or keep under `handlers/policy` — **depth first, taxonomy second** | Package name matches role |

**Anti-goals:** Big-bang rename PR; DI framework; multi-package “hexagon” skeleton empty of behavior.

---

## 6. Execution order (canonical)

```text
Phase 0  Stop bleeding (bans + board links)
   ↓
Phase 1  Collapse dual HAL → few deep capability surfaces
   ↓
Phase 2  Peel UI / peer / demo off controllers
   ↓
Phase 3  Pure policy extract + retype hurt call sites against those ports
   ↓
Phase 4  Status / composer deepen (opportunistic with consumers)
   ↓
Phase 5  Composition hygiene + light rehome
```

**Do not** expand a full port catalog and retype everything **before** Phase 2 peeling — that freezes shallow Protocols around polluted controller APIs.

**Do not** start Phase 5 renames before Phases 1–3 land real depth.

---

## 7. Slice template (every PR under this program)

Use this checklist in the PR / DEVNOTES entry:

```markdown
### TD-055.x — [title]

**Phase**: 0–5
**Complexity reduced** (pick ≥1):
- [ ] Change amplification (fewer edit sites for one intent)
- [ ] Cognitive load (fewer roles per type)
- [ ] Obscurity (honest names / one vocabulary)

**Depth check**:
- [ ] New/changed module has a simpler outward interface than before, or removes a dual path
- [ ] No pass-through-only type added
- [ ] No new second HAL / popup-on-controller / peer-on-controller

**Files**: …
**Validation**: pytest bands …
**QML contract**: frozen / delta: …
**Rollback**: revert PR; no data migration
```

---

## 8. Call-cluster inventory (updated 2026-07-29 — Phases 0–3)

| Consumer | Devices touched | Coupling after TD-055 0–3 | Surface |
|---|---|---|---|
| `ControlProcessor` | wheel, winch, teensy, valve | `SupportsWheelTeleop` / `SupportsWinchTeleop` / `SupportsTeensyTeleop` / `SupportsValveCommand` | continuous-motion ports |
| `WinchActions` / `WheelActions` | winch / wheel | typed capability Protocols; invoke lambdas (no string `method_name`) | motion/command ports + gate |
| `ManualCommandHandler` | teensy, winch | `SupportsManualTeensyCommands` + `SupportsWinchMotion`; demo via `run_demo_action` | ports + demo_sequence |
| `SafetyCoordinator` | winch, teensy halt, wheel, valve | halt Protocols (unchanged this slice) | `ports.halt` |
| Workflow adapters | teensy, winch, valve | thin adapters over shared ports; **no** `ITeensyController` / `IWinchController` ABCs | `ports.*` |
| Emergency / heartbeat | safety coordinator + devices | dual path residual left open (not this program) | coordinator preferred |
| Demo sequence | teensy + winch | `handlers/demo_sequence.run_demo_action` | application op |

---

## 9. Validation gates (program-wide)

For every implementation slice:

1. **Focused pytest** for touched modules (factory, ports consumers, workflow, safety, actions, control_processor as applicable).
2. **Full suite** before closing a phase (or when blast radius ≥ factory + multiple consumers).
3. **pyright** for covered Python scope when types/ports change.
4. **Startup smoke** only if QML-facing contracts change (prefer not to in Phases 0–3).
5. **No new context property** without last-consumer-proof retirement of something else (context freeze rule from `00_ARCHITECTURE_PROGRESS.md`).
6. **Teardown tests** if timers/threads/cleanup order change.

Baseline reference: follow current full-suite practice in `00_ARCHITECTURE_PROGRESS.md` / DEVNOTES.

---

## 10. Success metrics

This program is **done enough** when:

| Metric | Target |
|---|---|
| Hardware vocabulary | One primary definition site for Teensy/Winch (and touched) capabilities used by workflow + teleop + safety |
| Controllers as devices | No UI popup dependency; no peer-device fields for orchestration/demo on Teensy |
| Policy depth | Admin legality + teleop maps testable as plain Python |
| Hurt call sites | `ControlProcessor` and primary Actions not depending on `Any`/string method dispatch for the retyped surface |
| Shallow types | No net increase in pass-through-only façades “for architecture” |
| Names | Worst lies documented or fixed; no mandatory mega-rename |

Optional stretch (not required to close program): light rehome of presentation package names.

---

## 11. Cross-links (out of primary scope)

| Topic | Where it lives | Relation |
|---|---|---|
| QML context freeze / façade ownership | TD-032 closed; TD-047; `00_ARCHITECTURE_PROGRESS` | Preserve; do not reopen mega-retirement |
| Shared Teensy ports seed | TD-049 resolved | Phase 1 extends the pattern |
| Post-halt teleop inhibit residual | TD-046 residual | May use deeper ControlProcessor later; not Phase 0–2 blocker |
| Concurrent ROS publish + spin | TD-054 | Separate integrity program; do not expand multi-thread publish |
| Action legality field defaults | settings / product safety track | Not this plan’s success metric |
| Durable Qt architecture rationale | `01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md` | North-star product architecture; this plan is the Problem 2 execution program |

---

## 12. Rollback philosophy

- Prefer **forward fixes** within a phase.
- Each slice is independently revertable.
- Dual HAL merge: keep temporary adapter shims if needed; delete shims in the same phase before claiming done.
- Never leave **two permanent** hardware vocabularies “for compatibility” without an explicit quarantine note and retirement date in this file.

---

## 13. First slice recommendation (when implementation is approved)

**Start with Phase 0.1–0.3 (docs/process) + Phase 1.1 inventory**, then the smallest Phase 1.2 merge that unifies **workflow Teensy body** with existing `ports.teensy` (already seeded by TD-049).  

That maximizes depth (one vocabulary) with minimal risk and avoids premature full-port catalogs.

**Do not** open Phase 5 renames first.  
**Do not** retype all Actions before Phase 2 peels Teensy of popup/winch.

---

## 14. Document history

| Date | Change |
|---|---|
| 2026-07-29 | Initial plan from multi-perspective architecture review + Ousterhout (*A Philosophy of Software Design*) critique of Problem 2 improvement steps |
