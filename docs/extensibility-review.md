# Extensibility Code Review

> Review focus: how easy is it to change or add features to `paint_controller_ros2`?
> This document captures findings from emulating four common extension paths.

## Overall Verdict

The codebase has clear layer boundaries (QML → `*Actions` → gate → controllers; continuous-teleop catalog; TD-054/TD-056 threading models). That clarity is good, but it is paid for with a lot of **manual wiring**. Adding almost anything non-trivial touches 7–15 files and requires keeping several string/name/order lists in sync. Tests catch most drift, but only after the fact.

The biggest payoff would come from small registries or code-generation for the cross-layer contracts.

---

## Path 1 — Add a New Controller Family (e.g., Drone)

### Current Steps

1. `python/paint_controller/controllers/drone.py` — subclass `RosStatusController`, bind publishers through `RosCommandBus`, use `RosTelemetryBridge`.
2. `python/paint_controller/ports/drone.py` — define `SupportsDroneCommands` protocol.
3. `python/paint_controller/core/controller_factory.py` — import, construct in `_build_device_adapters()`, pass to the halt matrix if needed, add to `ControllerBundle`, add to `_CLEANUP_ORDER`, return in `create_controllers()`.
4. `python/paint_controller/models/drone_status.py` + `models/drone_actions.py` — wrap status and gated slots.
5. `python/paint_controller/core/qml_context_composer.py` — add `"droneStatus"` / `"droneActions"` to `_EXPECTED_CONTEXT_PROPERTY_NAMES` and to `compose()`.
6. `python/paint_controller/models/capability_catalog.py` — add entries to `_ACTION_CAPABILITIES`.
7. Update ~5–8 test files plus `tests/startup_smoke_support.py`.

**Total: ~12–20 files.**

### Friction

- `_CLEANUP_ORDER`, `ControllerBundle` fields, factory builder outputs, and `create_controllers()` kwargs must agree; tests enforce this, but they are the safety net.
- Status wrappers are pure boilerplate: snake_case controller signal → camelCase QML property with `connect_required()`.
- The action key string (`"drone.takeoff"`) is duplicated in `*Actions._run`, capability catalog, QML `actionKey`, and possibly `ACTION_METADATA_OVERRIDES`.

### Improvement Ideas

1. **Controller registry** — let a controller module register itself (class, bundle field name, cleanup order weight, action/status classes). `controller_factory.py` then iterates the registry.
2. **Schema-driven context properties** — one declarative list produces both `_EXPECTED_CONTEXT_PROPERTY_NAMES` and the `compose()` dict.
3. **Auto-generated status wrappers** — a small generator from `(signal_name, property_name, type)` tuples would eliminate the most repetitive file.
4. **Integrity test: action/catalog parity** — assert every `action_key` used in `*Actions` classes has a catalog entry and resolves to a real slot.

---

## Path 2 — Add a New Discrete Toggle Button / Command

### Current Steps

1. Add `@Slot` methods to the relevant `models/*_actions.py` (or create a new `*Actions` class).
2. Add the action key to `capability_catalog.py::_ACTION_CAPABILITIES`.
3. Add the action key string in the QML `actionKey` property and the slot call.
4. Wire the new `*Actions` object through `ControllerBundle`, factory, `QmlContextComposer`, `_EXPECTED_CONTEXT_PROPERTY_NAMES`, `MainWindow.qml` model aliases, and `tests/startup_smoke_support.py`.

**Total: ~7–10 files, ~200–250 lines for one button if it is a new action family.**

### Friction

- The string `"drone.hover"` lives in **4–5 places**: catalog, `*Actions._run`, QML `actionKey`, QML slot call, optional override.
- `ControlPanel.actionAllowed` defaults to `true` when `actionKey` is empty or `legalityModel` is null, so a wiring mistake looks "allowed."
- Gate enforcement is **convention**, not framework: forgetting `admin_action_gate.check_action()` in `_run` bypasses safety silently.
- `"authority"` in the catalog is decorative; nothing verifies it points to the real slot.

### Improvement Ideas

1. **Decorator-driven action registration**:
   ```python
   @action("drone.hover", legal_state_class="status-admin", title="Drone Hover")
   def toggleHover(self): ...
   ```
   This could auto-wrap the gate, register the catalog entry, and expose the slot.
2. **Typed action keys** — replace raw strings with a `Literal` or enum so typos fail at type-check / lint time.
3. **Runtime QML/Python contract test** — parse QML for `actionKey:` and `*Actions.*()` calls, then assert catalog + slot existence.
4. **Small `Action` command objects** — own `key`, `title`, `invoke`, `gate_check` to remove duplicated `_run` boilerplate across `*Actions` classes.

---

## Path 3 — Add a New Continuous Teleop Mode

### Current Steps

1. `python/paint_controller/handlers/policy/teleop_modes.py` — add label to `_MENU_LABELS`, display name to `_DISPLAY_NAMES`, apply function to `_STANDARD_APPLY` (or special handler mapping), config to `build_control_configs()`, policy flags.
2. `python/paint_controller/utils/constants.py` — add `JoystickControl` enum member.
3. `python/paint_controller/handlers/policy/teleop_control_map.py` + `handlers/continuous_teleop_engine.py` — plumb new scale/interval constants.
4. Controller: add continuous publisher + command method (e.g., `TeensyController.setDroneThrottle`).
5. `python/paint_controller/ports/teensy.py` — add protocol method.
6. `handlers/control_processor.py` — settings defaults and possibly display formatting.
7. Update fakes and teleop/catalog integrity tests.

**Total: ~7–11 files for a STANDARD mode; more for SPECIAL.**

### Friction

- The catalog is described as the single source of truth, but a new mode still touches **six internal tables/sets** in `teleop_modes.py` plus the enum. Integrity tests catch drift, but it is still manual.
- Scale constants must flow through `TeleopScaleConstants`, engine `_setup_constants`, `_setup_controls`, and `ControlProcessor._load_limit_defaults` — easy to miss a step.
- `ControlProcessor.format_side()` needs per-mode branches for non-scalar units.

### Improvement Ideas

1. **Self-registering teleop modes** — one decorator produces menu label, display name, STANDARD/SPECIAL kind, config, policy flags, and handler key.
2. **Derive `JoystickControl` from the catalog** — generate the enum from `menu_labels()` + side channels; eliminate enum/catalog drift.
3. **Catalog-owned formatting** — add `format_fn` / `unit` to `ControlConfig` so `ControlProcessor` renders new modes without `elif`.
4. **Policy-driven engine dispatch** — engine asks the catalog for kind and dispatches through a registry, so SPECIAL modes do not need two registration points.

---

## Path 4 — Other Common Extensions

### 4A. New Settings Field

- Add schema entry in `python/paint_controller/core/settings.py::_SETTINGS_SCHEMA`.
- Add `_make_setting_pair("drone_hover_height")` for supported types.
- Optionally update `python/config/settings.json`.
- Add QML control in a settings sub-page and register it in `PageSettings.qml`.

**Friction**: schema + property pair are two manual steps; only `float`/`int` have a generic `ManagedSettingSpinBox` QML component; route summaries are hand-written Python.

**Improvement**: auto-generate property pairs from `_SETTINGS_SCHEMA`; add generic `applyVariant`/`setVariant`; provide `ManagedSettingToggle`/`List`.

### 4B. New Full-Page Route

- Add registry entry in `python/paint_controller/models/shell_router.py::DEFAULT_ROUTE_REGISTRY`.
- Create `PageDrone.qml` + `qmldir`.
- Wire into `MainWindow.qml` imports, model aliases, and `routeComponentMap`.

**Friction**: route list in Python and component map in QML are two sources of truth; `order` is a hard-coded integer; every page directory needs a `qmldir`.

**Improvement**: generate `routeComponentMap` from the registry by convention (e.g., `key + "PageComponent"`); auto-assign `order`; default missing icons.

### 4C. New Workflow Step

- Add port Protocol + controller method.
- Add adapter in `services/workflow/hardware.py` and `HardwareControllers`.
- Add `ActionHandler` subclass in `services/workflow/actions.py` and register it.
- Add description branch in `workflow_runner.py::_generate_action_description`.
- Update factory to pass new controller to `HardwareControllers.from_controllers(...)`.

**Friction**: action type knowledge is duplicated between handler and `_generate_action_description`; no central param schema, so YAML typos surface at runtime; scheduler still has winch-centric position/completion assumptions.

**Improvement**: declarative action schema (type → param spec + description template); plugin-style handler discovery; generalize scheduler position triggers beyond winch cable length.

---

## Cross-Cutting Themes

| Theme | Observation |
|---|---|
| **Stringly contracts** | Action keys, route keys, menu labels, context property names are raw strings duplicated across layers. |
| **Manual registry updates** | Almost every extension requires touching a central list: `_EXPECTED_CONTEXT_PROPERTY_NAMES`, `_CLEANUP_ORDER`, `ControllerBundle`, `DEFAULT_ROUTE_REGISTRY`, `_ACTION_CAPABILITIES`, `_MENU_LABELS`, `JoystickControl`. |
| **Tests catch drift, but don't prevent it** | Integrity tests are good, but they report breakage rather than removing duplication. |
| **QML ↔ Python is rigid** | Adding a new model family means factory → bundle → composer → expected names → MainWindow aliases → smoke fakes. |
| **Safety is mostly convention** | Gate check is inside each `*Actions._run`; continuous latch is automatic only if you flow through `ControlProcessor`. |

---

## Recommended Priority Order

1. **Action/catalog decorator or schema (highest ROI)** — kills the 4–5 place string duplication for every new button and makes gate enforcement automatic.
2. **Schema-driven context properties** — collapse `_EXPECTED_CONTEXT_PROPERTY_NAMES`, `compose()`, and smoke fakes into one definition.
3. **Self-registering controller + teleop registries** — remove the factory/enum/catalog manual lists.
4. **Auto-generate `*Status` wrappers** — removes the most repetitive per-device file.
5. **Declarative workflow action schema** — reduces handler/description duplication and enables YAML validation.

---

# Trade-off Analysis

For each proposed improvement, an agent investigated whether the friction is caused by badly written code or is an unavoidable trade-off of the current architecture, and what would be sacrificed by implementing the change.

---

## 1. Action/Catalog Decorator or Schema

### Root cause
**Deliberate trade-off that has become overweight, not simply bad code.**

The duplication across QML `actionKey`, `*Actions._run`, `capability_catalog.py`, and optional `action_legality.py` overrides exists because the layers are intentionally decoupled: the catalog is a Qt-exposed metadata store, actions are feature-root QObject boundaries, and QML is string-based. The current design also supports per-environment policy overrides (`ACTION_METADATA_OVERRIDES`) without touching actions or catalog.

However, the `authority` field in the catalog is decorative, and gate enforcement is convention-based—forgetting `admin_action_gate.check_action()` silently bypasses safety.

### What would be sacrificed by a full decorator
- **Import-time side effects** — registration decorators mutate global state during import, which conflicts with the test harness's namespace-only stubs.
- **PySide6/QML slot gotchas** — `@Slot` must remain the outermost decorator; a wrapping decorator can break QML introspection unless carefully preserved.
- **Static analysis** — pyright struggles with dynamically registered methods and metaclass-added attributes.
- **Coupling** — importing the catalog would require importing all action modules, increasing startup cost and test fragility.
- **Reviewability** — gate calls and catalog entries become hidden inside framework code.
- **Per-environment overrides** — harder to layer site-specific policy unless the registry supports overrides.

### Recommended path (partial implementation)
1. Introduce a typed `ActionKey` enum / `Literal` and use it in `*Actions._run`, catalog keys, and overrides.
2. Add an integrity test that verifies every gated `action_key` has a catalog entry, every catalog `authority` resolves to a real slot, and QML `actionKey` values match.
3. Optionally extract a `GatedActionMixin` to remove repeated `_run`/`_fail` boilerplate while keeping the gate call explicit.

**Verdict: partially implement. Do not build a full runtime decorator registry.**

---

## 2. Schema-Driven Context Properties

### Root cause
**Deliberate trade-off, not poor structure.**

`_EXPECTED_CONTEXT_PROPERTY_NAMES` exists as an explicit QML contract list that `AppRuntime` checks at runtime. The duplication between that list and `compose()` buys:
- An independently readable contract for QML.
- A runtime mismatch check.
- Freedom to construct values in `compose()` any way needed (multi-source wrappers, ports-sourced objects).

### What would be sacrificed by a naive schema
- **Weaker contract check** — if both the expected list and the composed dict derive from the same schema, the mismatch check becomes circular and always passes.
- **Static analysis** — `getattr(bundle, field_name)` erases types that explicit code currently preserves.
- **Not all entries fit** — about half the current context properties are composites (`systemControlServices`, `videoRuntime`, `recordingStatus`, `shellConnectivityStatus`) or ports-sourced (`qtBridge`, `shellState`, etc.). A simple three-tuple schema cannot express them without becoming a DSL.
- **Smoke fakes** — a schema can tell the harness which fake class to use, but cannot generate the fake's signals/slots/properties automatically.
- **Ownership/lifetime** — a schema-driven factory must preserve the existing Python-strong-reference ownership model to avoid premature QObject collection.

### Recommended path (partial implementation)
Use a `ContextProp` hierarchy in `qml_context_composer.py`:
- `BundleProp` for simple passthroughs (`wheelActions`, `winchActions`, etc.).
- `WrapperProp` with explicit builder callables for status wrappers and composites.
- Derive `_EXPECTED_CONTEXT_PROPERTY_NAMES` from the schema.
- Add tests comparing schema names against `compose()` keys, smoke fakes, and `MainWindow.qml` aliases.

**Verdict: partially implement for simple entries; keep composite wrappers explicit.**

---

## 3. Self-Registering Controller + Teleop Registries

### Root cause
**Deliberate, defensible trade-off.**

`controller_factory.py` is an explicit dependency-graph description: `ControllerBundle` is a typed dataclass, `_CLEANUP_ORDER` is safety-critical, and subsystem builders group construction by dependency layer. Different controllers need different constructor args and init-time side effects (e.g., `ESP32ValveController` launches a UDP thread at `__init__`).

The teleop side is already centralized: `teleop_modes.py` is the single source of truth with invariant checks. The remaining manual sync points (`JoystickControl` enum, engine `_control_handlers`) are small and actively guarded by tests.

### What would be sacrificed by self-registration
- **Construction order** — `SafetyCoordinator`, `ControlProcessor`, and `EmergencyButtonHandler` need explicit partial orders that a registry cannot express without reintroducing a dependency language.
- **Cleanup order safety** — `_CLEANUP_ORDER` protects ROS/Qt teardown; a registry would need attachable teardown priorities and would make deterministic tests harder.
- **Type safety** — `ControllerBundle` would become a dynamic dict, losing IDE/autocomplete and pyright coverage.
- **Testability** — monkeypatching and constructing controller subsets becomes fragile with global registries.
- **Hidden import side effects** — self-registration only runs on import, causing controllers to register even in tests that only want the module.
- **Debuggability** — the runtime graph becomes discoverable only by running the program.

### Recommended path
- **Reject full self-registration for controllers.**
- **Keep the teleop catalog explicit.** If desired, code-generate `JoystickControl` from `teleop_modes.py` to close the last enum sync gap.
- An optional intermediate: an explicit `core/controller_registry.py` dict of factory lambdas imported by `controller_factory.py` — but this is only worth it if new devices are added frequently.

**Verdict: reject. The explicit factory and catalog are the better engineering choice for this codebase.**

---

## 4. Auto-Generate `*Status` Wrappers

### Root cause
**Deliberate architectural trade-off.**

The wrappers enforce a clear controller→QML boundary with per-property `NOTIFY`, fail-loud wiring (`status_wiring.connect_required`), and device-specific coercion. They are the explicit output of TD-037. Different devices genuinely need different shapes: `WheelStatus`/`WinchStatus` read scalar attributes, while `TeensyStatus` mixes a 43-field dict snapshot with 6 user-controlled bools.

### What would be sacrificed by a naïve generator
- **Per-property custom logic** — `TeensyStatus` does dict diffing, user-field preservation, and controller-property refresh that a simple schema cannot express.
- **Static analysis / QML introspection** — metaclass-generated attributes can be invisible to pyright and PySide6 unless carefully designed.
- **NOTIFY naming** — mappings are not purely mechanical camelCase (e.g., `load_detection_changed` → `loadDetectionEnabledChanged`).
- **Computed/derived fields** — hand-written classes make these trivial; generic wrappers need escape hatches.
- **Debugging** — stack traces land in generated code rather than named getters.

### Recommended path (partial implementation)
1. Introduce a schema-driven base/helper for the four "simple direct-attribute" wrappers (`Wheel`, `Winch`, `Valve`, `Lidar`).
2. Keep `TeensyStatus` hand-written because its semantics do not fit a simple schema.
3. Add an AST-based integrity test (like `test_settings_schema.py`) verifying schema-to-property parity.

**Verdict: partially implement. This is lower priority than items 1 and 2.**

---

## 5. Declarative Workflow Action Schema

### Root cause
**Mostly poor structure, with a reasonable separation of concerns.**

Keeping execution (handlers) separate from presentation (runner descriptions) is sensible. However, the **type-to-param mapping** is duplicated in three places: handler param extraction/defaults, runner description branches, and scheduler/QML form logic. There is no central contract, so YAML typos surface at runtime.

### What would be sacrificed by a full declarative DSL
- **Expressiveness of descriptions** — runner uses small conditional narratives ("Open valve to X" vs "Close valve") that a pure template language loses unless it grows conditionals.
- **Localization** — central templates are English literals today; l10n would require planning.
- **DSL complexity** — conditionals, derived params, and hardware-dependent durations need either a mini-language or code hooks.
- **Coupling** — a bad schema change propagates to editor, runner, executor, and scheduler.
- **Not all logic fits** — `estimate_duration` and scheduler position triggers need current winch length and runtime policy; these need code hooks.

### Recommended path (partial implementation)
Build a lightweight central `ActionType` registry in `services/workflow/action_schema.py`:
- `name`, `param_spec`, `description_template` (or `description_fn` hook), `handler_factory`, `metadata` flags (`is_winch_action`, `supports_position_trigger`).
- Refactor `ActionRegistry` to populate from the schema.
- Drive `_generate_action_description` from the schema template, keeping timing/trigger suffix logic in the runner and preserving explicit `description` overrides.
- Use `param_spec` in `WorkflowEditor._normalize_action_data` for early validation.
- Move scheduler winch detection from hardcoded type tuples to schema metadata.

**Verdict: partially implement with a registry + code hooks. Do not build a full DSL.**

---

## Updated Priority and Risk Table

| # | Improvement | Root Cause | Sacrifices if Done Naïvely | Recommended Scope |
|---|---|---|---|---|
| 1 | Action/catalog decorator or schema | Trade-off overweight | Import-time side effects, PySide6 introspection, static analysis, reviewability | Typed `ActionKey` + integrity test + optional mixin |
| 2 | Schema-driven context properties | Deliberate trade-off | Circular contract check, type erasure, composite-wrapper complexity | `ContextProp` hierarchy for simple entries; keep composites explicit |
| 3 | Self-registering controller + teleop registries | Deliberate trade-off | Construction/cleanup determinism, type safety, testability, debuggability | **Reject** full self-registration; consider code-gen for enum only |
| 4 | Auto-generate `*Status` wrappers | Deliberate trade-off | Custom logic loss, static-analysis blind spots, debugging friction | Base/helper for simple wrappers; keep `TeensyStatus` custom |
| 5 | Declarative workflow action schema | Poor structure | DSL overkill, localization burden, coupling | Central `ActionType` registry with templates + code hooks |

---

## Final Takeaway

The biggest extensibility pain is not "bad code" — it is **manual synchronization across layer boundaries**. The highest-ROI, lowest-risk fixes are:

1. **Typed action keys + integrity tests** — removes string drift without runtime magic.
2. **Schema-driven context-property list for simple entries** — removes one manual sync point while keeping the contract check meaningful.

Items 3 and 4 should be limited in scope because the current explicit structures serve real safety, type-safety, and debuggability goals. Item 5 is worthwhile but should be implemented as a registry with code hooks, not a pure declarative DSL.
