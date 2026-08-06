# PySide6 / Qt Performance Plan — Decision Board

> Created: 2026-08-06  
> Status: **Research complete — user selects which items to apply**  
> Scope: Performance opportunities for this Python-first PySide6/QML + ROS2 app on Steam Deck.  
> Authority: Does **not** supersede `01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md` or `AGENTS.md`. Architecture invariants win over micro-optimizations.

---

## How to use this document

1. Read **Design non-negotiables** and **Already applied**.
2. Review each **P-item** (candidate).
3. For each item, mark a decision in the summary table:
   - **Apply** — schedule implementation
   - **Defer** — valid but not now
   - **Reject** — wrong for this product / violates design
4. Prefer **measure first** (P-00) before large structural items (P-01, P-02).

This is a **menu**, not a committed roadmap. Nothing here is approved for implementation until you pick items.

---

## Problem restatement

Improve runtime performance (UI smoothness, CPU/thermal headroom, video latency, main-thread budget) of the paint controller without:

- collapsing discrete admin vs continuous teleop into one API
- moving policy/safety/actuator math into QML
- introducing a mega-`Backend` or ambient god object
- moving the teleop loop onto RosThread
- reintroducing blanket status `changed` storms or `qmlRegisterSingletonInstance`

---

## Research summary — highest-leverage techniques (general)

From industry Qt6/QML + PySide guidance, ranked for a Steam Deck–class device with ~60 Hz teleop + multi-camera video + ROS:

| Rank | Technique | Typical impact |
|------|-----------|----------------|
| 1 | Keep UI-thread Python work small (≤2–5 ms/frame) | High |
| 2 | Per-property NOTIFY; never blanket `changed` | High |
| 3 | Coalesce high-rate telemetry to display rate | High |
| 4 | Marshal ROS→UI via QueuedConnection / POD snapshots | High |
| 5 | Frame-skip video workers (drop, don’t queue) | High |
| 6 | Lazy QML (Loader / unload obscured trees) | High |
| 7 | Avoid layer/clip/DropShadow on hot paths | High when present |
| 8 | `QAbstractListModel` + granular updates for large lists | Med–High |
| 9 | QThread for I/O; processes only for pure-Python CPU | High |
| 10 | Profile on target (QML Profiler + py-spy + `QSG_*`) | Meta |

**Measurement-first rule:** optimize from evidence on the Deck. Qt’s own first tip is QML Profiler — don’t guess.

---

## Current architecture snapshot (performance-relevant)

| Path | Rate | Affinity | Owner |
|------|------|----------|--------|
| Continuous teleop | Status timer **60 Hz** | Qt main | `SignalWiring._on_status_tick` → `ControlProcessor` → `ContinuousTeleopEngine` |
| Discrete admin | Event | Qt main + gate | `*Actions` + `AdminActionGate` |
| HID | ~100 Hz | Worker thread | `SteamDeckReaderThread` |
| ROS spin + command pump | continuous | `RosThread` | `ros_node.py` + `RosCommandBus` |
| Telemetry ROS→Qt | last-wins | Post any; apply main | `RosTelemetryBridge` |
| Video decode | per frame ×N cams | GStreamer threads | `CameraStream` / `ImageProvider` |
| Base-top vision | on enable | Worker + frame-skip | `BaseTopViewService` |
| System metrics | 1 Hz | Worker | `SystemMonitor` |

Default operator surface: **fullscreen video overlay** (`VideoFullscreenWorkspace`), not page chrome. Dual-monitor can mount a second overlay stack.

Config: `RuntimeDefaults.update_rate = 60.0` (`core/config.py`).

---

## Design non-negotiables (filter)

Any candidate that fails these is **Reject** regardless of FPS gain:

| # | Invariant | Source |
|---|-----------|--------|
| 1 | No mega-`Backend`; composition bag + inject | AGENTS.md, arch plan anti-goals |
| 2 | QML declarative; Python owns safety/hardware/ROS/policy | AGENTS.md |
| 3 | Discrete gated path **≠** continuous teleop path | AGENTS.md dual control paths |
| 4 | Do **not** move teleop onto RosThread | tech-debt.md research non-goals |
| 5 | No MultiThreadedExecutor-first rewrite / process split as “perf program” | tech-debt.md |
| 6 | Per-property NOTIFY only (no blanket status storm) | AGENTS.md |
| 7 | ROS commands for continuous/oneshot: bus pump on RosThread | TD-054 |
| 8 | ROS→Qt: no unlocked QObject mutation from spin thread | TD-056 |
| 9 | Safety order on status tick: e-stop / exit-hold **before** teleop | TD-054 / `signal_wiring.py` |
| 10 | `setContextProperty` over `qmlRegisterSingletonInstance` | KNOWLEDGE.md |

---

## Already applied (do not re-implement as “new” work)

| Technique | Where |
|-----------|--------|
| Frame-skip (`_processing`) on base-top OpenCV | `base_top_view_service.py` |
| Lazy connect/disconnect of `frameReady` when `enabled` | `BaseTopViewService` |
| Per-mode HW command rate limits (0.1–0.3 s) + deadzone stop | `ContinuousTeleopEngine` |
| Display string throttle 5 Hz | `ControlProcessor.MESSAGE_UPDATE_INTERVAL` |
| `RosCommandBus` continuous last-wins | `ros_io.py` |
| `RosTelemetryBridge` last-wins + QueuedConnection | `ros_telemetry.py` |
| Per-property device status façades | `TeensyStatus`, `SimpleDeviceStatus`, … |
| HID poll reduced to 10 ms | `steam_deck.py` |
| Deferred video start (+200 ms after timers) | `signal_wiring.py` |
| Video `Connections` gated by `root.active` | `VideoFullscreenWorkspace.qml` |
| Map recompute coalesce timer | TD-039 |
| Dedicated workers for HID / GStreamer / SSH pool / system monitor | various |

---

## Decision summary table

Mark each row after review:

| ID | Title | Impact (est.) | Effort | Design risk | Decision |
|----|-------|---------------|--------|-------------|----------|
| **P-00** | Measurement baseline (before any opt) | Meta | S | None | **Apply-done** (`utils/perf_counters.py`) |
| **P-01** | Video: cut double-copy + QML cache-bust | **High** | M–L | Low if Python still owns pixels | **Apply-done** (generation URL, option B) |
| **P-02** | Lazy / demand-driven multi-stream GStreamer | **High** | M | Low if `videoRuntime` owns policy | **Apply-done** (option C warm EF+front) |
| **P-03** | Status-tick idle early-out (keep 60 Hz e-stop) | Med–High | S–M | **Must preserve safety order** | **Apply-done** (skip engine when modes None) |
| **P-04** | Telemetry / status paint rate split | Med | M | Keep per-property NOTIFY | ☐ Apply / ☐ Defer / ☐ Reject |
| **P-05** | Dual-surface video/binding gate | Med | M | Product dual-monitor rule | ☐ Apply / ☐ Defer / ☐ Reject |
| **P-06** | ImageProvider double-buffer / swap | Med–High | M | Thread safety critical | **Apply-done** (`publish` + COW `requestImage`) |
| **P-07** | Gate page-local QML timers on visibility | Low–Med | S | None | ☐ Apply / ☐ Defer / ☐ Reject |
| **P-08** | Startup: defer base-top worker / heavy shells | Med (cold start) | M | Keep factory graph | ☐ Apply / ☐ Defer / ☐ Reject |
| **P-09** | QML scene hygiene (overdraw, effects, text) | Med when effects | S–M | Chrome only; no policy | ☐ Apply / ☐ Defer / ☐ Reject |
| **P-10** | Large list models → `QAbstractListModel` | Low–Med *here* | M | Prefer only if lists hurt | ☐ Apply / ☐ Defer / ☐ Reject |
| **P-11** | Thermal/idle rate scaling | Med (battery) | M | Product policy in Python | ☐ Apply / ☐ Defer / ☐ Reject |

**Recommended pick order if you want a short list:**  
`P-00` → profile → then likely `P-01`/`P-06` and/or `P-02` (video dominates) → `P-03` if tick budget shows up → small wins `P-07`/`P-09`.

---

## Candidate items (detail)

Each item: technique source · applicability · design check · tradeoffs · affected range · validation · decision.

---

### P-00 — Measurement baseline (do this first)

**Technique:** Profile before change (QML Profiler, py-spy, `QSG_VISUALIZE`, custom p50/p99 counters).

**Applicability:** Fully applicable. Current suite is offscreen and **does not** load real video/HID; device soak is required for real numbers.

**Design check:** Pass — instrumentation only; keep counters behind debug flags / settings.

**Tradeoffs:**

| Pro | Con |
|-----|-----|
| Prevents wrong rewrites | Needs Deck access + short operator scenarios |
| Creates regression budgets | Temporary code or scripts to maintain |
| Justifies which of P-01…P-11 matter | Profiler changes timing slightly |

**Affected range:**

| Layer | Paths |
|-------|--------|
| Optional debug | `SignalWiring._on_status_tick`, `CameraStream._on_new_sample`, `ImageProvider.requestImage` counters |
| Ops | shell notes / one-shot scripts (not permanent docs unless useful) |
| Tests | none required unless counters stay in production behind flag |

**Suggested budgets (edit after first measure):**

| Metric | Starter budget |
|--------|----------------|
| Status tick p95 (idle sticks) | ≤1–2 ms |
| Status tick p95 (active teleop) | ≤3–5 ms |
| Stick → command enqueue | product-defined (e.g. ≤20–50 ms) |
| Video display lag | prefer drop over queue; age &lt; 2–3 frames |
| Startup to interactive shell | product target |

**Validation:** Capture 30–60 s of worst workflow: teleop + fullscreen video + EF overlay + dual monitor if used.

**Decision:** ☐ Apply / ☐ Defer / ☐ Reject

---

### P-01 — Video path: reduce per-frame double copy + QML source cache-bust

**Technique:** Image provider / custom item; avoid full-frame copy on every request; prefer texture update over `source="" ; source=url` thrash.

**Evidence today:**

1. `CameraStream._on_new_sample` — `QImage.copy()` into provider + emit `frameReady` (`video_stream.py` ~171–178).
2. `ImageProvider.requestImage` — **another** `.copy()` under mutex (~88–94).
3. `VideoFullscreenWorkspace.qml` — on each `*FrameReady`, clear `source` then reassign `image://…/frame` (~282–305) while `root.active`.

That is **decode + 2× copy + scene-graph invalidate** per frame for the active feed (worse if multiple consumers).

**Applicability:** **High**. Largest evidence-backed UI/CPU risk in this tree after multi-stream decode.

**Design check:**

| Rule | OK? |
|------|-----|
| Python owns pixels / stream lifecycle | Yes — keep provider or custom item in services |
| No policy in QML | Yes — QML only displays |
| No mega-Backend | Yes |
| Dual path untouched | Yes |

**Tradeoffs:**

| Pro | Con |
|-----|-----|
| Major CPU/GPU savings at 30–60 fps | Lifetime/threading bugs if swap wrong |
| Lower thermal load on Deck | May need custom `QQuickItem` (more code than Image) |
| Better teleop latency feel | Must keep never-null / stale-clear behavior (TD-039 residual) |

**Options (choose implementation style if Apply):**

| Option | Idea | Risk |
|--------|------|------|
| A | Double-buffer swap in provider; `requestImage` returns shallow ref or last stable buffer without deep copy every time | Medium — must prove GStreamer can’t mutate returned image |
| B | Versioned URL (`image://ef_live/frame?v=N`) without full tree destroy | Lower than today if copy still needed |
| C | Custom QQuickItem uploading texture from worker | Higher effort; best long-term |

**Affected range:**

| Layer | Paths |
|-------|--------|
| Python | `services/video_stream.py` (`ImageProvider`, `CameraStream`), possibly `base_top_view_service.py` providers |
| QML | `qml/features/video/VideoFullscreenWorkspace.qml`, `qml/pages/wheel/PageWheel.qml` (same cache-bust), video overlay components that reassign source |
| Context | `videoRuntime` / feeds signals if refresh API changes |
| Tests | `tests/test_video_stream.py`, video smoke fixtures in `startup_smoke_support.py` if contract changes |

**Validation:** Device FPS/CPU before/after; freeze/stale after stream stop; switch EF↔base; dual window if applicable. Focused pytest video band.

**Decision:** ☐ Apply / ☐ Defer / ☐ Reject  
**If Apply, preferred option:** ☐ A / ☐ B / ☐ C / ☐ (decide after P-00)

---

### P-02 — Lazy / demand-driven multi-stream GStreamer

**Technique:** Don’t run pipelines you aren’t displaying; event-driven connect; one stream owner.

**Evidence today:** Deferred start still calls **start all enabled streams** (EF + base front/top/rear configs). Base-top may decode even when OpenCV path is disabled.

**Applicability:** **High** if product allows warm-start latency on camera switch.

**Design check:**

| Rule | OK? |
|------|-----|
| Ownership in Python `videoRuntime` / handler | Required — not QML “if visible stop stream” policy for hardware |
| Reuse one stream signal (no duplicate subs) | Keep |
| Seamless EF↔base switch | Product call: warm vs cold |

**Tradeoffs:**

| Pro | Con |
|-----|-----|
| Large multi-core / thermal win on Deck | First frame lag when switching cameras |
| Idle battery savings | Need explicit “must stay warm” set (e.g. current + preview) |
| Aligns with lazy-connect knowledge | More state machine (starting/stopping/error) |

**Sub-options:**

| Option | Behavior |
|--------|----------|
| A | Only active `videoSource` pipeline playing; stop others after grace period |
| B | Keep last two sources warm (active + previous) for fast toggle |
| C | Always warm EF + base front; lazy rear/top only |

**Affected range:**

| Layer | Paths |
|-------|--------|
| Python | `services/video_stream.py` (`start_all_streams`, start/stop API), `app_runtime` deferred video, any `videoRuntime` façade |
| QML | ideally **no** policy; may need “loading” indicator binding only |
| Tests | video start/stop tests; smoke deferred startup |

**Validation:** Mode switch latency; no zombie pipelines; e-stop/UI still work without video; CPU with one vs four streams.

**Decision:** ☐ Apply / ☐ Defer / ☐ Reject  
**If Apply, preferred option:** ☐ A / ☐ B / ☐ C

---

### P-03 — Status-tick idle early-out (preserve safety + 60 Hz e-stop)

**Technique:** Separate timer rates / reduce UI-thread work when idle; continuous path stays off gate.

**Evidence today:** `status_timer` always fires at 60 Hz → `_on_status_tick` always: HID snapshot → emergency → exit-hold → `process_input` (even sticks centered). Engine rate-limits **publishes**, not necessarily full main-thread mode walk.

**Applicability:** **Medium–High** if P-00 shows tick &gt; budget when idle.

**Design check:**

| Rule | OK? |
|------|-----|
| Do **not** move teleop to RosThread | Must not |
| E-stop / exit-hold before teleop | **Must keep every tick** (or equivalent ≤16 ms latency) |
| `continuous_motion_allowed` latch | Must keep |
| Not under AdminActionGate | Keep |

**Safe shape (if Apply):**

```
on_status_tick:
  poll e-stop + exit-hold always
  if motion allowed:
    if sticks active or mode needs hold/zero or winch ramp active:
      process_input full
    else:
      lightweight idle (deadzone trackers / zero-hold as required)
  # display already throttled at 5 Hz
```

**Unsafe shapes (Reject):**

- Skipping e-stop poll to save CPU
- Putting teleop publish on RosThread callbacks
- Merging teleop into gated `*Actions`

**Tradeoffs:**

| Pro | Con |
|-----|-----|
| Free main-thread headroom for video/QML | Complexity in “what counts as idle” |
| Better under thermal throttle | Risk of missing zero-on-release if idle logic wrong |
| Keeps 60 Hz safety poll | Needs strong unit tests for track partner-hold, winch lock, halt |

**Affected range:**

| Layer | Paths |
|-------|--------|
| Python | `core/signal_wiring.py`, `handlers/control_processor.py`, `handlers/continuous_teleop_engine.py`, possibly `emergency.py` / `exit_hold.py` only for call order docs |
| QML | none expected |
| Tests | `test_control_processor*`, teleop track/winch lifecycle, emergency latency tests if any |

**Validation:** Full teleop band + e-stop hold while sticks full-scale; track mode partner hold; post-halt stick must not re-drive.

**Decision:** ☐ Apply / ☐ Defer / ☐ Reject

---

### P-04 — Telemetry / status paint rate split

**Technique:** Coalesce high-rate telemetry to display rate; command path stays high rate.

**Evidence today:** Telemetry already last-wins to main. Device façades use per-property NOTIFY. Dense `TeensyStatus` (and similar) can still fan out many binding updates to EF overlays at firmware rate.

**Applicability:** **Medium** — helps when overlays/status pages open and firmware is chatty; less critical if only sparse HUD.

**Design check:**

| Rule | OK? |
|------|-----|
| Per-property NOTIFY (not one mega signal) | Required |
| Truthful status (don’t invent values) | Throttle paint, not corrupt HAL |
| No policy in QML | Throttle in Python façade/apply |

**Tradeoffs:**

| Pro | Con |
|-----|-----|
| Calmer QML bindings on video overlays | UI numbers update less often (10–15 Hz usually fine) |
| Fits existing bridge pattern | Epsilon/equality checks for floats |
| Doesn’t touch teleop commands | Wrong place: don’t throttle HAL internal state used by safety |

**Affected range:**

| Layer | Paths |
|-------|--------|
| Python | `models/*_status.py`, shell apply paths, possibly teensy status apply |
| QML | consumers auto-benefit; no logic move |
| Tests | status model unit tests; optional emit-rate assertions |

**Validation:** Overlay open under load; property emit/sec before/after; no safety path reading stale throttled copy incorrectly.

**Decision:** ☐ Apply / ☐ Defer / ☐ Reject

---

### P-05 — Dual-surface video / binding gate

**Technique:** Draw less; only active surface pays full refresh cost.

**Evidence today:** Product dual-monitor: main + industrial secondary can each host `ShellOverlayStack` / video consumers against the same providers/signals.

**Applicability:** **Medium** — only if dual monitor is used often and both refresh full-rate video.

**Design check:**

| Rule | OK? |
|------|-----|
| Built-in = touch/control; external = mission | Product invariant stays |
| Python owns screen-role / host policy | Prefer gate in host policy, not ad-hoc QML |
| Shared composition stack | Don’t fork two video architectures |

**Tradeoffs:**

| Pro | Con |
|-----|-----|
| Halves video invalidate work when one surface is text-only | Need product rule: which surface gets live video |
| Saves GPU on Deck APU | Industrial monitor may require always-on video by design |

**Affected range:**

| Layer | Paths |
|-------|--------|
| Python | screen manager / overlay host / videoRuntime “active surfaces” |
| QML | `ShellOverlayStack.qml`, `MainWindow.qml`, `MultiScreenHost.qml`, video workspace `enabled` gates |
| Tests | multi-screen smoke if present |

**Validation:** Dual on/off; touch controls remain on built-in; no double `frameReady` work when secondary doesn’t show video.

**Decision:** ☐ Apply / ☐ Defer / ☐ Reject

---

### P-06 — ImageProvider double-buffer / swap (subset of P-01)

**Technique:** Buffer reuse; reduce allocations/GC; thread-safe swap.

**Note:** Can be done as a **slice of P-01** without changing QML refresh mechanism. Listed separately so you can apply a safer half-step.

**Applicability:** High if P-01 full redesign deferred.

**Design check:** Pass if never-null and lock discipline preserved.

**Tradeoffs:**

| Pro | Con |
|-----|-----|
| Cuts one deep copy + alloc churn | Still pays QML cache-bust if P-01 QML half skipped |
| Smaller PR than full custom item | Subtle use-after-free if QML holds image while writer swaps wrong |

**Affected range:** Primarily `services/video_stream.py` (+ base-top provider if shared pattern).

**Validation:** Same as video band; stress rapid stream stop/start.

**Decision:** ☐ Apply / ☐ Defer / ☐ Reject  
*(If P-01 Apply with option A/C, this may fold into P-01.)*

---

### P-07 — Gate page-local QML timers on visibility

**Technique:** Stop timers when inactive.

**Evidence:** e.g. `DigitalGauge.qml` history timer `running: true` while component exists; other page timers (PageWheel) may run when not needed.

**Applicability:** **Low–Medium** local win; cheap.

**Design check:** Pass — pure presentation; no model-mutating cosmetic slots (KNOWLEDGE).

**Tradeoffs:**

| Pro | Con |
|-----|-----|
| Easy CPU save when pages live off-screen | Easy to break “live chart while overlay open” if gate wrong |
| No architecture change | Must use `visible` / `Window` / parent active, not opacity alone |

**Affected range:**

| Layer | Paths |
|-------|--------|
| QML | `qml/components/displays/DigitalGauge.qml`, page timers in wheel/winch/status as found |
| Python | none |
| Tests | optional visual/unit; smoke if components in load path |

**Decision:** ☐ Apply / ☐ Defer / ☐ Reject

---

### P-08 — Startup cold path: defer heavy workers until needed

**Technique:** Lazy init / chain load after first paint.

**Evidence:** Controllers + GStreamer init before deferred streams; base-top worker thread may start even when processing disabled; MainWindow warmup Loaders trade cold-start for nav.

**Applicability:** Medium for **time-to-interactive**; less for steady-state FPS.

**Design check:**

| Rule | OK? |
|------|-----|
| AppRuntime remains composition root | Yes |
| No import-time self-registering controllers | Yes |
| Explicit factory graph | Keep — defer *start*, not hide construction |

**Tradeoffs:**

| Pro | Con |
|-----|-----|
| Faster first shell paint | First enable of base-top / camera pays latency |
| Lower idle RAM | More “not ready yet” states to handle |

**Affected range:** `app_runtime.py`, `BaseTopViewService.__init__`/enable, possibly controller factory “start” vs “construct”, QML warmup Loaders only if re-evaluated.

**Validation:** Startup logs (`_log_startup` stages); first-use of base-top/video; teardown still clean (timer/thread cleanup tests).

**Decision:** ☐ Apply / ☐ Defer / ☐ Reject

---

### P-09 — QML scene graph hygiene (overdraw, effects, text)

**Technique:** Less overdraw; avoid casual `layer`/`DropShadow`/`clip` on hot paths; prefer PlainText; anchors over binding soup.

**Applicability:** Medium **if** `QSG_VISUALIZE=overdraw` or batches show pain. MainWindow already warms ChartView/DropShadow — polish effects may be present on chrome.

**Design check:** Chrome-only; no policy in QML; no “one skin” mega program (TD-002 out of band).

**Tradeoffs:**

| Pro | Con |
|-----|-----|
| GPU/batch wins on Deck | Visual polish tradeoff |
| Aligns with KDAB/Spyrosoft QML tips | Easy to bikeshed design system |

**Affected range:** QML chrome/overlays/components with effects; not Python contracts.

**Validation:** `QSG_VISUALIZE` before/after; visual QA on Deck 7″ + external.

**Decision:** ☐ Apply / ☐ Defer / ☐ Reject

---

### P-10 — Large dynamic lists → `QAbstractListModel`

**Technique:** Granular model updates instead of full JS array replace.

**Applicability:** **Low–Medium in this product** today — workflow editor / tuning lists exist, but operator path is video+teleop, not huge virtualized lists. Apply only if profiling shows ListView/Repeater thrash (e.g. workflow editor with large action lists).

**Design check:** Model ownership in Python; QML declarative; co-locate schema with owner (AGENTS deep module).

**Tradeoffs:**

| Pro | Con |
|-----|-----|
| Correct pattern for large tables | Boilerplate; wrong begin/end = view corruption |
| Future-proof editor scale | Little win if N is small |

**Affected range:** Workflow editor models, tuning lists, status logs — only the list you profile.

**Decision:** ☐ Apply / ☐ Defer / ☐ Reject

---

### P-11 — Thermal / idle rate scaling

**Technique:** Lower rates when idle / on battery (Deck).

**Applicability:** Medium for field battery life; product policy decision.

**Design check:** Policy in Python (settings or power state from `SystemMonitor`); continuous teleop may stay aggressive when sticks active; never weaken e-stop poll.

**Tradeoffs:**

| Pro | Con |
|-----|-----|
| Battery + thermals | “Why is video choppy on battery?” support load |
| Uses existing power status signals | More modes to test |

**Affected range:** `config` / settings, `signal_wiring` or videoRuntime rate knobs, `SystemMonitor` consumers.

**Decision:** ☐ Apply / ☐ Defer / ☐ Reject

---

## Explicitly rejected “optimizations” (do not schedule)

| Temptation | Why rejected |
|------------|--------------|
| Mega-`Backend` “to reduce context property lookups” | Ambient coupling; anti-goal |
| Policy / legality / actuator math in QML “to avoid Python slots” | Safety + untestable; not real speed for policy |
| Collapse teleop + admin into one Action API | Wrong affinity and safety model |
| Move continuous teleop loop onto RosThread | Explicit non-goal; affinity / latch / bus design |
| MultiThreadedExecutor rewrite as first move | Non-goal; complexity without proven need |
| UI process / control process split | Non-goal |
| Blanket `statusChanged` to “simplify signals” | Binding storms; violates per-property NOTIFY |
| `qmlRegisterSingletonInstance` for “faster access” | Known type-system risk in this repo |
| `processEvents` / nested loops to “keep UI alive” | Re-entrancy crashes |
| Queue all video frames “to never drop” | Latency death spiral for teleop |
| Thread pure-Python math for GIL speedup | GIL; measure first; prefer less work |

---

## Suggested phased packages (only after you select items)

These are **optional packaging** suggestions, not a commitment:

| Package | Items | Goal |
|---------|-------|------|
| **Baseline** | P-00 | Numbers on Deck |
| **Video A** | P-06 then P-01 | Steady-state CPU/FPS |
| **Video B** | P-02 ± P-05 | Multi-stream / dual surface |
| **Main-thread** | P-03 ± P-04 | Teleop tick + status calm |
| **Polish** | P-07, P-09 | Cheap local wins |
| **Cold start** | P-08 | Time-to-shell |
| **Power** | P-11 | Battery |

Do **not** merge Video A + main-thread + architecture debt slices in one PR.

---

## Validation gates (any Apply)

Per `AGENTS.md`:

1. Focused pytest band for touched boundary, then broader if multi-area.
2. pyright on covered Python scope.
3. Offscreen smoke if QML contracts / context properties change.
4. **Device soak** for video/teleop items (CI cannot replace Deck load).
5. Safety: e-stop latency and post-halt stick inhibit must remain correct for P-03/P-02/P-11.

---

## Ousterhout × professional Qt check

This plan reduces **change amplification** by:

- keeping video ownership in one service family
- keeping teleop on the existing continuous path
- throttling paint at status façades rather than inventing a new global bus

It reduces **unknown unknowns** by:

- measurement first (P-00)
- listing hard rejects so “clever” shortcuts don’t ship

It does **not** introduce mega-façades or policy-in-QML for speed.

---

## User decision checklist

Please reply with which IDs to **Apply**, and for multi-option items your preferred option:

```
P-00: 
P-01:   option:
P-02:   option:
P-03: 
P-04: 
P-05: 
P-06: 
P-07: 
P-08: 
P-09: 
P-10: 
P-11: 
```

After you decide, implementation will follow the normal Plan → Confirm → Implement workflow for the selected slice only (one family at a time).

---

## References (research)

| Source | Topic |
|--------|--------|
| [Qt Quick Performance](https://doc.qt.io/qt-6/qtquick-performance.html) | Official QML performance |
| [Qt Property System](https://doc.qt.io/qt-6/properties.html) | NOTIFY / bindings |
| [Threads and QObjects](https://doc.qt.io/qt-6/threads-qobject.html) | Thread affinity |
| [QQuickImageProvider](https://doc.qt.io/qt-6/qquickimageprovider.html) | Live images |
| [KDAB: 10 QML tips (2024)](https://www.kdab.com/10-tips-to-make-your-qml-code-faster-and-more-maintainable/) | Modern QML speed |
| [Spyrosoft QML perf](https://spyro-soft.com/expert-hub/qt-quick-qml-performance-optimisation) | Effects/overdraw case studies |
| Project: `AGENTS.md`, `KNOWLEDGE.md`, `docs/plan/01_…`, `docs/tech-debt.md` | Local invariants |

---

## Evidence map (code anchors)

| Topic | Anchor |
|-------|--------|
| 60 Hz status timer | `core/signal_wiring.py` `start_timers` / `_on_status_tick` |
| update_rate | `core/config.py` `RuntimeDefaults.update_rate = 60.0` |
| Teleop façade | `handlers/control_processor.py` |
| Engine rate limits | `handlers/continuous_teleop_engine.py` |
| Video copy + provider | `services/video_stream.py` |
| QML cache-bust | `qml/features/video/VideoFullscreenWorkspace.qml` |
| Telemetry bridge | `core/ros_telemetry.py` |
| Command bus | `core/ros_io.py` (via TD-054) |
| Base-top frame-skip | `services/base_top_view_service.py` |
