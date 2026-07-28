# TD-034 Plan: Make the colcon Build Gate Real

> **Status**: draft v2 — audited (verdict: NEEDS MODIFICATION → accepted with two overrides), ready for approval
> **Lifecycle**: delete this file when TD-034 closes (per AGENTS.md Pruning Policy)
> **Tech-debt**: `docs/tech-debt.md` TD-034 (high)
> **Stop-and-ask**: modifies `CMakeLists.txt` — plan approval by the user covers this trigger.
> **Audit highlights**: fix-by-deletion independently reproduced green in a `/tmp` workspace; zero consumers of the install payload repo- and workspace-wide. v1's CI step was broken: lint is red on `dev` today (1965 ruff errors, 111 format failures) and `build` declares `needs: lint`, so the colcon gate would have been silently skipped.

## Goal

`colcon build --packages-select paint_controller_ros2` green locally and in CI, with the dead packaging half-truths removed.

## Decision

**Fix by deletion, not restructure.** The app runs from the source tree by design (hand-written bash launcher + venv); nothing reads `share/paint_controller_ros2/` anywhere in the workspace; install-space deployment is explicitly non-viable today (TD-036). Proper ament packaging is out of scope — if deployment ever changes, that is a new project, not this TD.

## Approach

1. **`CMakeLists.txt`**: remove the `resource/` install stanza (broken) **and** the `qml/` install stanza (works, but nothing reads it — dead installs are how this normalized). Remove the now-orphaned `# Install directories` comment; add a one-line comment: "intentionally installs no payload — the app runs from the source tree." Keep `ament_package()` (auto-registers the ament-index marker; no `resource/` marker needed for `ament_cmake`) and the lint block.
2. **Housekeeping** (exact commands, run before rebuild — colcon will not remove the stale payload itself):
   `rm -rf ~/ros2_ws/build/paint_controller_ros2 ~/ros2_ws/install/paint_controller_ros2`
3. **Verify**: `cd ~/ros2_ws && source /opt/ros/jazzy/setup.bash && colcon build --packages-select paint_interfaces paint_controller_ros2` green from the clean tree; `colcon list` still finds the package.
4. **`setup.cfg`**: delete the whole file (it contains only the stale ament_python `[develop]`/`[install]` sections — inert for pip, misleading to readers).
5. **CI — the corrected version**:
   - Add `dev` to the workflow trigger branches (keep existing entries).
   - **Remove `needs: lint` from the `build` job** so the colcon gate runs even while lint is red — otherwise enabling `dev` recreates normalized-red with the gate skipped (the audit's central finding).
   - **Explicitly descoped**: making the lint/test/typecheck jobs green on `dev`. At execution time, file two new tech-debt entries: (a) ruff debt on `dev` (1965 errors / 111 format failures — not currently tracked); (b) CI test/typecheck runner dependencies (`PyGObject` has no binary wheels; no apt steps for girepository/cairo/Qt runtime libs).
6. **`package.xml`**: no change (deps are truthful rosdep metadata; the CI build job's `rosdep install` relies on them).
7. **Docs at completion**: move TD-034 to the Resolved table in `docs/tech-debt.md`; sweep README and `docs/plan/00_ARCHITECTURE_PROGRESS.md` for any statement that the build "fails pre-existingly" and correct it. (Dated DEVNOTES entries stay — they are time-stamped history per the Pruning Policy.)

## Files

- `CMakeLists.txt` (stop-and-ask — covered by plan approval)
- `setup.cfg` (delete)
- `.github/workflows/ci.yml`
- `docs/tech-debt.md` (at completion)

## Validation gates

- `colcon build --packages-select paint_interfaces paint_controller_ros2` succeeds from a clean `build/`+`install/` for this package.
- CI YAML parses; `build` job no longer depends on `lint`.
- Full pytest suite unaffected (no runtime code touched).

## Risks

- **Hidden consumer of the install payload** — ruled out by the audit (repo-wide and workspace-wide grep; launcher only needs `paint_interfaces` from the install tree). Residual risk accepted.
- **`dev` CI will show red lint/test dashboards** until the two new debt entries are addressed — that is surfacing real debt, not a regression; the colcon gate itself runs independently.

## Rollback

`git revert` the three files; re-run housekeeping commands in reverse is unnecessary (install payload was dead).
