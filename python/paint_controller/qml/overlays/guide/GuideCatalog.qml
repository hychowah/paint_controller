import QtQuick

/**
 * Context-keyed operator guide packs.
 *
 * Each pack is only meaningful on its matching surface:
 *   ef              — EF video chrome active
 *   base            — BASE video chrome active
 *   system_devices  — System Control → Devices
 *   system_command  — System Control → Command
 *   system_settings — System Control → Settings
 *   system_workflow — System Control → WorkFlow (runner)
 *   workflow_editor — full-page workflow editor
 *   deck_buttons    — Steam Deck hardware buttons (not screen chrome)
 *
 * Anchors are relative (0–1) to the host that mounts OperatorGuideOverlay.
 * deck_buttons uses empty hotspots + centered callouts (no UI target).
 *
 * Deck-button binding facts (which control, double-press window) are owned in
 * Python: DEFAULT_DOUBLE_PRESS_THRESHOLD_S (utils/input.py) and
 * DEFAULT_EXIT_HOLD_DURATION_S (handlers/exit_hold.py). Integrity test pins
 * catalog tokens to those constants — do not invent alternate timings here.
 */
QtObject {
    id: catalog

    readonly property var contextTitles: ({
        "ef": "EF video",
        "base": "BASE video",
        "system_devices": "Devices",
        "system_command": "Command",
        "system_settings": "Settings",
        "system_workflow": "WorkFlow",
        "workflow_editor": "Workflow editor",
        "deck_buttons": "Deck buttons"
    })

    function titleFor(contextId) {
        return contextTitles[contextId] || contextId || "Guide"
    }

    function stepsFor(contextId) {
        switch (contextId) {
        case "base":
            return baseSteps
        case "system_devices":
            return systemDevicesSteps
        case "system_command":
            return systemCommandSteps
        case "system_settings":
            return systemSettingsSteps
        case "system_workflow":
            return systemWorkflowSteps
        case "workflow_editor":
            return workflowEditorSteps
        case "deck_buttons":
            return deckButtonSteps
        case "ef":
        default:
            return efSteps
        }
    }

    // --- EF video HUD ---
    readonly property var efSteps: [
        {
            id: "ef_switch_mode",
            title: "EF mode is active",
            body: "You are on the end-effector camera and joystick layout. Tap BASE in the top bar to switch camera and restore the BASE stick layout.",
            hotspots: [
                { x: 0.01, y: 0.01, w: 0.14, h: 0.08 },
                { x: 0.82, y: 0.01, w: 0.16, h: 0.08 }
            ],
            calloutX: 0.48,
            calloutY: 0.20
        },
        {
            id: "ef_hud",
            title: "EF overlay readouts",
            body: "Pitch is end-effector tilt. Valve panel shows position, flow, and volume. Wall detection shows distance, angle deviation, and signal. EXT / GIMBAL sit near the left tile.",
            hotspots: [
                { x: 0.38, y: 0.08, w: 0.24, h: 0.16 },
                { x: 0.80, y: 0.30, w: 0.18, h: 0.22 },
                { x: 0.36, y: 0.78, w: 0.28, h: 0.16 }
            ],
            calloutX: 0.28,
            calloutY: 0.40
        },
        {
            id: "ef_left",
            title: "Left stick mode",
            body: "Press L4 or tap LEFT CONTROL. D-pad Up/Down to move, A or tap to select. EF modes include arm, top rail, spray pitch/trigger, force, and more.",
            hotspots: [{ x: 0.02, y: 0.82, w: 0.18, h: 0.15 }],
            calloutX: 0.06,
            calloutY: 0.52
        },
        {
            id: "ef_right",
            title: "Right stick mode",
            body: "Press R4 or tap RIGHT CONTROL. Track Left/Right can sit on both sticks; other modes are exclusive to one side.",
            hotspots: [{ x: 0.80, y: 0.82, w: 0.18, h: 0.15 }],
            calloutX: 0.42,
            calloutY: 0.50
        },
        {
            id: "ef_system",
            title: "System Control",
            body: "Tap the hamburger for Devices, Command, Settings, and WorkFlow. Open the WorkFlow tab for Play/Stop; open Edit there for the full editor guide (only available on that screen).",
            hotspots: [{ x: 0.01, y: 0.42, w: 0.08, h: 0.12 }],
            calloutX: 0.14,
            calloutY: 0.38
        },
        {
            id: "ef_to_buttons",
            title: "Hardware buttons",
            body: "Thrust force, arm extend/retract, base move, and exit app are Steam Deck buttons — not on this screen. Tap the Btn control (above ?) for that guide.",
            hotspots: [],
            calloutX: 0.28,
            calloutY: 0.35
        }
    ]

    // --- BASE video HUD ---
    readonly property var baseSteps: [
        {
            id: "base_switch_mode",
            title: "BASE mode is active",
            body: "You are on the base camera and track-oriented joystick layout. Tap EF in the top bar to switch camera and restore the EF stick layout.",
            hotspots: [
                { x: 0.01, y: 0.01, w: 0.14, h: 0.08 },
                { x: 0.82, y: 0.01, w: 0.16, h: 0.08 }
            ],
            calloutX: 0.48,
            calloutY: 0.20
        },
        {
            id: "base_hud",
            title: "BASE overlay readouts",
            body: "Left motor tiles show RPM, current, and travel. Base top view is the overhead fisheye. Winch current/cable sit near the right tile when winch is assigned.",
            hotspots: [
                { x: 0.18, y: 0.55, w: 0.22, h: 0.28 },
                { x: 0.72, y: 0.28, w: 0.22, h: 0.32 }
            ],
            calloutX: 0.30,
            calloutY: 0.18
        },
        {
            id: "base_left",
            title: "Left stick mode",
            body: "Press L4 or tap LEFT CONTROL. On BASE, Track Control Left/Right and wheel travel modes are common. D-pad Up/Down, then A or tap to select.",
            hotspots: [{ x: 0.02, y: 0.82, w: 0.18, h: 0.15 }],
            calloutX: 0.06,
            calloutY: 0.52
        },
        {
            id: "base_right",
            title: "Right stick mode",
            body: "Press R4 or tap RIGHT CONTROL. Winch speed and track modes often live here. Track can share both sticks; other modes are exclusive.",
            hotspots: [{ x: 0.80, y: 0.82, w: 0.18, h: 0.15 }],
            calloutX: 0.42,
            calloutY: 0.50
        },
        {
            id: "base_system",
            title: "System Control",
            body: "Hamburger opens Devices (power, winch, wheel), Command, Settings, and WorkFlow. Workflow editing has its own guide once you open Edit.",
            hotspots: [{ x: 0.01, y: 0.42, w: 0.08, h: 0.12 }],
            calloutX: 0.14,
            calloutY: 0.38
        },
        {
            id: "base_to_buttons",
            title: "Hardware buttons",
            body: "Thrust force, arm extend/retract, base move, and exit app are Steam Deck buttons — not on this screen. Tap the Btn control (above ?) for that guide.",
            hotspots: [],
            calloutX: 0.28,
            calloutY: 0.35
        }
    ]

    // --- System Control tabs ---
    // Anchors are relative to the centered System Control dialog panel
    // (systemMenuContainer ~800×700), not the full window.
    readonly property var systemDevicesSteps: [
        {
            id: "sys_tabs",
            title: "System Control tabs",
            body: "Devices, Command, Settings, and WorkFlow live in this bar. This guide follows the tab you have open — switch tab and tap ? again for that tab’s tips.",
            hotspots: [{ x: 0.04, y: 0.10, w: 0.92, h: 0.09 }],
            calloutX: 0.12,
            calloutY: 0.24
        },
        {
            id: "sys_power",
            title: "Hardware power",
            body: "Teensy Relay and Teensy Enable power the EF stack. Toggles are gated; legality and connection status show under each row.",
            hotspots: [{ x: 0.05, y: 0.22, w: 0.90, h: 0.30 }],
            calloutX: 0.12,
            calloutY: 0.55
        },
        {
            id: "sys_winch_wheel",
            title: "Winch and wheel",
            body: "Expand Winch for enable and load detection. Expand Wheel for motor controls. Use Show/Hide on each section card.",
            hotspots: [{ x: 0.05, y: 0.52, w: 0.90, h: 0.30 }],
            calloutX: 0.12,
            calloutY: 0.28
        }
    ]

    readonly property var systemCommandSteps: [
        {
            id: "sys_cmd",
            title: "Command tab",
            body: "Manual / discrete commands for the active hardware live here (not continuous teleop). Use this when you need one-shot moves or admin actions from the menu.",
            hotspots: [{ x: 0.05, y: 0.20, w: 0.90, h: 0.60 }],
            calloutX: 0.12,
            calloutY: 0.10
        }
    ]

    readonly property var systemSettingsSteps: [
        {
            id: "sys_settings",
            title: "Settings tab",
            body: "Persistent operator settings. Changes go through confirmation where required. Teleop physics and device config stay in Python — this tab only presents and writes settings.",
            hotspots: [{ x: 0.05, y: 0.20, w: 0.90, h: 0.60 }],
            calloutX: 0.12,
            calloutY: 0.10
        }
    ]

    readonly property var systemWorkflowSteps: [
        {
            id: "wf_select",
            title: "Select a workflow",
            body: "Pick a saved workflow from the dropdown. Status stays Idle until you Play. Actions list fills once a workflow is loaded.",
            // WorkFlow label + combo (top of content well)
            hotspots: [{ x: 0.06, y: 0.20, w: 0.72, h: 0.16 }],
            calloutX: 0.10,
            calloutY: 0.42
        },
        {
            id: "wf_play_stop",
            title: "Play and Stop",
            body: "Play runs the loaded sequence. Stop aborts. These controls only appear meaningful after a workflow is selected.",
            hotspots: [{ x: 0.52, y: 0.48, w: 0.42, h: 0.28 }],
            calloutX: 0.08,
            calloutY: 0.42
        },
        {
            id: "wf_edit",
            title: "Edit opens the editor",
            body: "Tap Edit to open the full-page workflow editor. The detailed step-palette guide only appears there — open ? on the editor screen.",
            hotspots: [{ x: 0.74, y: 0.20, w: 0.20, h: 0.10 }],
            calloutX: 0.12,
            calloutY: 0.36
        }
    ]

    // --- Steam Deck hardware buttons (video host; no UI hotspots) ---
    // Owned by input / exit_hold handlers — not screen widgets.
    readonly property var deckButtonSteps: [
        {
            id: "btn_overview",
            title: "Hardware buttons",
            body: "These actions are bound to Steam Deck buttons, not on-screen controls. They work on the video HUD whether EF or BASE is active. Stick modes (L4/R4) stay in the EF/BASE guides.",
            badge: "Deck",
            hotspots: [],
            calloutX: 0.28,
            calloutY: 0.28
        },
        {
            id: "btn_thrust",
            title: "Thrust force",
            body: "Press L1 to toggle thrust force on/off. A popup confirms enabled or disabled. This is discrete (not a stick mode).",
            badge: "L1",
            hotspots: [],
            calloutX: 0.28,
            calloutY: 0.28
        },
        {
            id: "btn_arm",
            title: "Extend / retract arm",
            // DOUBLE_PRESS_WINDOW token must match DEFAULT_DOUBLE_PRESS_THRESHOLD_S
            body: "Double-press R5 to extend the arm to the configured extend length. Double-press L5 to retract to the configured retract length. First press shows a hint; second press within ~1s runs the command. Lengths come from settings.",
            badge: "L5 / R5",
            hotspots: [],
            calloutX: 0.28,
            calloutY: 0.26
        },
        {
            id: "btn_base_pos",
            title: "Move base position",
            // DOUBLE_PRESS_WINDOW token must match DEFAULT_DOUBLE_PRESS_THRESHOLD_S
            body: "Double-press A to send the wheel travel position command (base move-to target). First press shows a hint; second press within ~1s sends. When a joystick menu is open, A also confirms the highlighted row.",
            badge: "A ×2",
            hotspots: [],
            calloutX: 0.28,
            calloutY: 0.26
        },
        {
            id: "btn_exit",
            title: "Exit app",
            // Duration owned by DEFAULT_EXIT_HOLD_DURATION_S — do not hard-code seconds here.
            body: "Hold the Switch button to quit. Keep holding until the exit progress overlay completes, then release. Releasing early cancels. SteamOS Steam button is separate and is not used for app exit.",
            badge: "⋯ Switch",
            hotspots: [],
            calloutX: 0.28,
            calloutY: 0.26
        },
        {
            id: "btn_menus",
            title: "Related buttons",
            body: "Menu opens System Control. L4 / R4 open left / right stick mode menus. D-pad navigates those menus. Those are covered in the EF/BASE video guides (?).",
            badge: "Menu · L4 · R4",
            hotspots: [],
            calloutX: 0.28,
            calloutY: 0.28
        }
    ]

    // --- Workflow editor full page ---
    readonly property var workflowEditorSteps: [
        {
            id: "ed_palette",
            title: "Add steps from the palette",
            body: "Left column: Winch Increment/Absolute, Valve, Spray Gimbal, Arm Extend, EF Force, Wait, Parallel group. Tap a type to append a step.",
            hotspots: [{ x: 0.01, y: 0.12, w: 0.22, h: 0.80 }],
            calloutX: 0.28,
            calloutY: 0.30
        },
        {
            id: "ed_list",
            title: "Steps run in order",
            body: "Center list is the sequence. Enable Loop in the top bar to repeat after the last step. Select a step to edit parameters on the right.",
            hotspots: [{ x: 0.24, y: 0.12, w: 0.48, h: 0.80 }],
            calloutX: 0.28,
            calloutY: 0.20
        },
        {
            id: "ed_params",
            title: "Step parameters",
            body: "Right panel shows fields for the selected step. Use Up / Down / Delete step to reorder or remove. Parallel groups have member pickers.",
            hotspots: [{ x: 0.74, y: 0.12, w: 0.25, h: 0.80 }],
            calloutX: 0.30,
            calloutY: 0.35
        },
        {
            id: "ed_save",
            title: "Save and Back",
            body: "Save / Save as persist the document. Back returns to System Control WorkFlow where you can Play the saved sequence.",
            hotspots: [{ x: 0.01, y: 0.01, w: 0.98, h: 0.10 }],
            calloutX: 0.25,
            calloutY: 0.20
        }
    ]
}
