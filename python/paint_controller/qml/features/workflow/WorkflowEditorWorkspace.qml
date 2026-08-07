import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../theme"
import "../../overlays/systemcontrol/components" as SysComponents
import "../../components/inputs"
import "../../overlays/guide"

/**
 * Full-page touch workflow editor.
 * Python owns the document session (workflowEditor); this surface is chrome + slots only.
 *
 * Typography and touch targets are sized for Steam Deck 7″ (1280×800) at arm’s length:
 * floor ≥13px, primary controls 16–18px, field values emphasized.
 */
Rectangle {
    id: root
    objectName: "workflowEditorWorkspace"

    required property var workflowEditor
    required property var overlayController

    readonly property bool editorActive: workflowEditor ? workflowEditor.is_open : false
    readonly property bool operatorGuideOpen: editorGuideHost.open

    function openOperatorGuide(startIndex) {
        editorGuideHost.openGuide("workflow_editor", startIndex || 0)
    }

    function closeOperatorGuide() {
        editorGuideHost.closeGuide()
    }

    onEditorActiveChanged: {
        if (!editorActive)
            closeOperatorGuide()
    }
    readonly property int selectedIndex: workflowEditor ? workflowEditor.selected_index : -1
    readonly property int selectedMemberIndex: workflowEditor ? workflowEditor.selected_member_index : -1
    readonly property var stepsModel: workflowEditor ? workflowEditor.steps : []
    readonly property var paletteModel: workflowEditor ? workflowEditor.palette : []
    readonly property var memberPaletteModel: workflowEditor ? workflowEditor.member_palette : []
    readonly property var selectedStep: {
        if (!workflowEditor || selectedIndex < 0 || selectedIndex >= stepsModel.length)
            return null
        return stepsModel[selectedIndex]
    }
    readonly property var selectedMember: {
        if (!selectedStep || selectedStep.kind !== "parallel")
            return null
        if (!selectedStep.members || selectedMemberIndex < 0
                || selectedMemberIndex >= selectedStep.members.length)
            return null
        return selectedStep.members[selectedMemberIndex]
    }
    property bool memberTypeChooserOpen: false
    property bool memberAddChooserOpen: false

    // Local type ladder (Steam Deck readability; uses CommonStyle scaleFactor only)
    readonly property int fontTitle: Math.round(22 * CommonStyle.scaleFactor)
    readonly property int fontSection: Math.round(18 * CommonStyle.scaleFactor)
    readonly property int fontPrimary: Math.round(16 * CommonStyle.scaleFactor)
    readonly property int fontStepTitle: Math.round(17 * CommonStyle.scaleFactor)
    readonly property int fontSecondary: Math.round(14 * CommonStyle.scaleFactor)
    readonly property int fontField: Math.round(18 * CommonStyle.scaleFactor)
    readonly property int fontFloor: Math.round(13 * CommonStyle.scaleFactor)

    visible: editorActive
    anchors.fill: parent
    color: CommonStyle.backgroundL0
    z: 1100

    // Block touches to surfaces underneath
    MouseArea {
        anchors.fill: parent
        enabled: root.editorActive
        onClicked: {}
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Math.round(12 * CommonStyle.scaleFactor)
        spacing: Math.round(10 * CommonStyle.scaleFactor)

        // Top bar
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: Math.round(68 * CommonStyle.scaleFactor)
            color: CommonStyle.backgroundL1
            radius: CommonStyle.radiusMd
            border.color: CommonStyle.borderDefault
            border.width: 1

            RowLayout {
                anchors.fill: parent
                anchors.margins: Math.round(10 * CommonStyle.scaleFactor)
                spacing: Math.round(10 * CommonStyle.scaleFactor)

                EditorButton {
                    text: "← Back"
                    buttonWidth: Math.round(120 * CommonStyle.scaleFactor)
                    onClicked: {
                        if (workflowEditor)
                            workflowEditor.close_editor()
                    }
                }

                Text {
                    text: (workflowEditor ? workflowEditor.workflow_name : "Workflow")
                          + (workflowEditor && workflowEditor.is_dirty ? " *" : "")
                    color: CommonStyle.textPrimary
                    font.pixelSize: root.fontTitle
                    font.bold: true
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                    verticalAlignment: Text.AlignVCenter
                }

                CheckBox {
                    id: loopBox
                    text: "Loop"
                    checked: workflowEditor ? workflowEditor.loop : false
                    onCheckedChanged: {
                        if (workflowEditor && checked !== workflowEditor.loop)
                            workflowEditor.set_loop(checked)
                    }
                    contentItem: Text {
                        text: loopBox.text
                        color: CommonStyle.textPrimary
                        font.pixelSize: root.fontPrimary
                        leftPadding: loopBox.indicator.width + 8
                        verticalAlignment: Text.AlignVCenter
                    }
                }

                EditorButton {
                    text: "New"
                    buttonWidth: Math.round(88 * CommonStyle.scaleFactor)
                    onClicked: {
                        if (workflowEditor)
                            workflowEditor.new_document("untitled")
                    }
                }

                EditorButton {
                    text: "Load"
                    buttonWidth: Math.round(96 * CommonStyle.scaleFactor)
                    onClicked: loadPopup.open()
                }

                EditorButton {
                    text: "Save"
                    buttonWidth: Math.round(96 * CommonStyle.scaleFactor)
                    accent: true
                    enabled: workflowEditor && workflowEditor.workflow_name !== ""
                    onClicked: {
                        if (workflowEditor)
                            workflowEditor.save()
                    }
                }

                EditorButton {
                    text: "Save as"
                    buttonWidth: Math.round(110 * CommonStyle.scaleFactor)
                    onClicked: saveAsKeyboard.openFor(workflowEditor ? workflowEditor.workflow_name : "")
                }

                EditorButton {
                    objectName: "workflowEditorHelpButton"
                    text: "?"
                    buttonWidth: Math.round(56 * CommonStyle.scaleFactor)
                    visible: !root.operatorGuideOpen
                    onClicked: root.openOperatorGuide(0)
                }
            }
        }

        // Main body
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: Math.round(10 * CommonStyle.scaleFactor)

            // Palette
            Rectangle {
                Layout.preferredWidth: Math.round(200 * CommonStyle.scaleFactor)
                Layout.fillHeight: true
                color: CommonStyle.backgroundL1
                radius: CommonStyle.radiusMd
                border.color: CommonStyle.borderDefault
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: Math.round(10 * CommonStyle.scaleFactor)
                    spacing: 8

                    Text {
                        text: "Add step"
                        color: CommonStyle.textPrimary
                        font.bold: true
                        font.pixelSize: root.fontSection
                    }

                    ListView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        spacing: 8
                        model: root.paletteModel
                        delegate: EditorButton {
                            width: ListView.view.width
                            height: Math.round(62 * CommonStyle.scaleFactor)
                            text: modelData.label || modelData.type
                            onClicked: {
                                if (workflowEditor)
                                    workflowEditor.add_step(modelData.type)
                            }
                        }
                    }
                }
            }

            // Step timeline
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: CommonStyle.backgroundL1
                radius: CommonStyle.radiusMd
                border.color: CommonStyle.borderDefault
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: Math.round(10 * CommonStyle.scaleFactor)
                    spacing: 8

                    RowLayout {
                        Layout.fillWidth: true
                        Text {
                            text: "Steps (" + root.stepsModel.length + ")"
                            color: CommonStyle.textPrimary
                            font.bold: true
                            font.pixelSize: root.fontSection
                            Layout.fillWidth: true
                        }
                        Text {
                            text: workflowEditor && workflowEditor.loop ? "∞ Loop enabled" : "Ends after last step"
                            color: workflowEditor && workflowEditor.loop ? "#AAFFAA" : CommonStyle.textSecondary
                            font.pixelSize: root.fontSecondary
                        }
                    }

                    ListView {
                        id: stepsList
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        spacing: 8
                        model: root.stepsModel

                        delegate: Rectangle {
                            width: stepsList.width
                            height: Math.round(84 * CommonStyle.scaleFactor)
                            radius: 8
                            color: root.selectedIndex === index ? "#3A5A8C" : CommonStyle.backgroundL2
                            border.color: root.selectedIndex === index ? "#5A7AAC" : CommonStyle.borderDefault
                            border.width: 1

                            MouseArea {
                                anchors.fill: parent
                                onClicked: {
                                    if (workflowEditor)
                                        workflowEditor.select_step(index)
                                }
                            }

                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 4

                                RowLayout {
                                    Layout.fillWidth: true
                                    Text {
                                        text: (index + 1) + ". " + stepTitle(modelData)
                                        color: CommonStyle.textPrimary
                                        font.bold: true
                                        font.pixelSize: root.fontStepTitle
                                        Layout.fillWidth: true
                                        elide: Text.ElideRight
                                    }
                                    Text {
                                        text: stepKindBadge(modelData)
                                        color: CommonStyle.textSecondary
                                        font.pixelSize: root.fontFloor
                                    }
                                }
                                Text {
                                    text: stepSummary(modelData)
                                    color: CommonStyle.textSecondary
                                    font.pixelSize: root.fontSecondary
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                }
                            }
                        }
                    }
                }
            }

            // Inspector (slightly wider for parallel member tools)
            Rectangle {
                Layout.preferredWidth: Math.round(340 * CommonStyle.scaleFactor)
                Layout.fillHeight: true
                color: CommonStyle.backgroundL1
                radius: CommonStyle.radiusMd
                border.color: CommonStyle.borderDefault
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: Math.round(12 * CommonStyle.scaleFactor)
                    spacing: 10

                    // Group identity
                    Text {
                        text: {
                            if (!root.selectedStep)
                                return "Select a step"
                            if (root.selectedStep.kind === "parallel")
                                return "Parallel group"
                            return "Edit step"
                        }
                        color: CommonStyle.textPrimary
                        font.bold: true
                        font.pixelSize: root.fontSection
                        Layout.fillWidth: true
                    }

                    Text {
                        visible: !!root.selectedStep && root.selectedStep.kind === "parallel"
                        text: "These actions start together"
                        color: CommonStyle.textSecondary
                        font.pixelSize: root.fontPrimary
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }

                    Text {
                        visible: !!root.selectedStep && root.selectedStep.kind !== "parallel"
                        text: root.selectedStep ? stepTitle(root.selectedStep) : ""
                        color: CommonStyle.textSecondary
                        font.pixelSize: root.fontSecondary
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }

                    // Continue policy
                    ColumnLayout {
                        visible: root.selectedStep && (root.selectedStep.kind === "action" || root.selectedStep.kind === "parallel")
                        Layout.fillWidth: true
                        spacing: 6
                        Text {
                            text: root.selectedStep && root.selectedStep.kind === "parallel"
                                  ? "When group finishes"
                                  : "After this step"
                            color: CommonStyle.textPrimary
                            font.pixelSize: root.fontSecondary
                            font.bold: true
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            EditorButton {
                                text: "Wait done"
                                Layout.fillWidth: true
                                height: Math.round(52 * CommonStyle.scaleFactor)
                                accent: root.selectedStep && root.selectedStep.continue === "wait_complete"
                                onClicked: {
                                    if (workflowEditor)
                                        workflowEditor.set_continue_policy("wait_complete")
                                }
                            }
                            EditorButton {
                                text: "Next now"
                                Layout.fillWidth: true
                                height: Math.round(52 * CommonStyle.scaleFactor)
                                accent: root.selectedStep && root.selectedStep.continue === "continue_immediately"
                                onClicked: {
                                    if (workflowEditor)
                                        workflowEditor.set_continue_policy("continue_immediately")
                                }
                            }
                        }
                    }

                    // Wait duration
                    ColumnLayout {
                        visible: root.selectedStep && root.selectedStep.kind === "wait"
                        Layout.fillWidth: true
                        spacing: 6
                        Text {
                            text: "Duration (ms)"
                            color: CommonStyle.textPrimary
                            font.pixelSize: root.fontSecondary
                        }
                        TextField {
                            id: waitField
                            Layout.fillWidth: true
                            Layout.preferredHeight: Math.round(56 * CommonStyle.scaleFactor)
                            readOnly: true
                            color: CommonStyle.textPrimary
                            font.pixelSize: root.fontField
                            font.bold: true
                            text: root.selectedStep && root.selectedStep.kind === "wait"
                                  ? String(root.selectedStep.duration_ms || "")
                                  : ""
                            background: Rectangle {
                                color: CommonStyle.backgroundL2
                                border.color: CommonStyle.borderFocused
                                radius: 6
                            }
                            MouseArea {
                                anchors.fill: parent
                                onClicked: {
                                    numpad.targetField = waitField
                                    numpad.paramKey = "duration_ms"
                                    numpad.memberIndex = -1
                                    numpad.open()
                                }
                            }
                        }
                    }

                    // Action params (simple key list)
                    Flickable {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        contentHeight: paramsColumn.implicitHeight
                        clip: true
                        visible: root.selectedStep && root.selectedStep.kind === "action"

                        ColumnLayout {
                            id: paramsColumn
                            width: parent.width
                            spacing: 10

                            Repeater {
                                model: root.selectedStep && root.selectedStep.params
                                       ? Object.keys(root.selectedStep.params)
                                       : []
                                delegate: ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 4
                                    Text {
                                        text: modelData
                                        color: CommonStyle.textSecondary
                                        font.pixelSize: root.fontSecondary
                                    }
                                    TextField {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: Math.round(56 * CommonStyle.scaleFactor)
                                        readOnly: true
                                        color: CommonStyle.textPrimary
                                        font.pixelSize: root.fontField
                                        font.bold: true
                                        text: root.selectedStep && root.selectedStep.params
                                              ? String(root.selectedStep.params[modelData])
                                              : ""
                                        background: Rectangle {
                                            color: CommonStyle.backgroundL2
                                            border.color: CommonStyle.borderFocused
                                            radius: 6
                                        }
                                        MouseArea {
                                            anchors.fill: parent
                                            onClicked: {
                                                numpad.targetField = parent
                                                numpad.paramKey = modelData
                                                numpad.memberIndex = -1
                                                numpad.open()
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }

                    // Parallel members (Python owns legality; chrome only)
                    Flickable {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        contentHeight: parallelColumn.implicitHeight
                        clip: true
                        visible: root.selectedStep && root.selectedStep.kind === "parallel"

                        ColumnLayout {
                            id: parallelColumn
                            width: parent.width
                            spacing: 12

                            Text {
                                text: {
                                    var n = root.selectedStep && root.selectedStep.members
                                            ? root.selectedStep.members.length : 0
                                    return "Actions (" + n + ")"
                                }
                                color: CommonStyle.textPrimary
                                font.bold: true
                                font.pixelSize: root.fontSecondary
                            }

                            Repeater {
                                model: root.selectedStep && root.selectedStep.members
                                       ? root.selectedStep.members
                                       : []
                                delegate: Rectangle {
                                    Layout.fillWidth: true
                                    height: Math.round(76 * CommonStyle.scaleFactor)
                                    color: index === root.selectedMemberIndex
                                           ? CommonStyle.backgroundL3
                                           : CommonStyle.backgroundL2
                                    radius: 6
                                    border.color: index === root.selectedMemberIndex
                                                  ? CommonStyle.borderFocused
                                                  : CommonStyle.borderDefault
                                    border.width: index === root.selectedMemberIndex ? 2 : 1

                                    // Left accent: selection vs lead (distinct)
                                    Rectangle {
                                        anchors.left: parent.left
                                        anchors.top: parent.top
                                        anchors.bottom: parent.bottom
                                        width: 4
                                        radius: 2
                                        color: {
                                            if (index === root.selectedMemberIndex)
                                                return CommonStyle.borderFocused
                                            if (index === 0)
                                                return CommonStyle.accentSecondary
                                            return "transparent"
                                        }
                                    }

                                    ColumnLayout {
                                        anchors.fill: parent
                                        anchors.leftMargin: 12
                                        anchors.rightMargin: 10
                                        anchors.topMargin: 8
                                        anchors.bottomMargin: 8
                                        spacing: 4

                                        RowLayout {
                                            Layout.fillWidth: true
                                            spacing: 8
                                            Text {
                                                text: actionTypeLabel(modelData.type)
                                                color: CommonStyle.textPrimary
                                                font.bold: true
                                                font.pixelSize: root.fontPrimary
                                                elide: Text.ElideRight
                                                Layout.fillWidth: true
                                            }
                                            // Lead badge (first member = wait-done target)
                                            Rectangle {
                                                visible: index === 0
                                                radius: 4
                                                color: "#2a4a3a"
                                                border.color: CommonStyle.accentSecondary
                                                border.width: 1
                                                implicitWidth: leadLabel.implicitWidth + 12
                                                implicitHeight: Math.round(22 * CommonStyle.scaleFactor)
                                                Text {
                                                    id: leadLabel
                                                    anchors.centerIn: parent
                                                    text: "Leads"
                                                    color: CommonStyle.textPrimary
                                                    font.pixelSize: root.fontFloor
                                                    font.bold: true
                                                }
                                            }
                                        }
                                        Text {
                                            text: memberSummary(modelData)
                                            color: CommonStyle.textSecondary
                                            font.pixelSize: root.fontSecondary
                                            elide: Text.ElideRight
                                            Layout.fillWidth: true
                                        }
                                    }
                                    MouseArea {
                                        anchors.fill: parent
                                        onClicked: {
                                            root.memberTypeChooserOpen = false
                                            root.memberAddChooserOpen = false
                                            if (workflowEditor)
                                                workflowEditor.select_member(index)
                                        }
                                    }
                                }
                            }

                            // Row 1: add / remove (full-width pair — avoids "Add Remove" crush)
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 10
                                EditorButton {
                                    text: root.memberAddChooserOpen ? "Cancel add" : "Add action"
                                    Layout.fillWidth: true
                                    height: Math.round(52 * CommonStyle.scaleFactor)
                                    onClicked: {
                                        root.memberTypeChooserOpen = false
                                        root.memberAddChooserOpen = !root.memberAddChooserOpen
                                    }
                                }
                                EditorButton {
                                    text: "Remove"
                                    Layout.fillWidth: true
                                    height: Math.round(52 * CommonStyle.scaleFactor)
                                    enabled: root.selectedStep && root.selectedStep.members
                                             && root.selectedStep.members.length > 1
                                             && root.selectedMemberIndex >= 0
                                    onClicked: {
                                        root.memberTypeChooserOpen = false
                                        root.memberAddChooserOpen = false
                                        if (workflowEditor)
                                            workflowEditor.remove_selected_member()
                                    }
                                }
                            }

                            // Row 2: who leads (first = wait-done target)
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 4
                                Text {
                                    text: "Who leads completion"
                                    color: CommonStyle.textSecondary
                                    font.pixelSize: root.fontFloor
                                }
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 10
                                    EditorButton {
                                        text: "Move up"
                                        Layout.fillWidth: true
                                        height: Math.round(48 * CommonStyle.scaleFactor)
                                        enabled: root.selectedMemberIndex > 0
                                        onClicked: {
                                            if (workflowEditor)
                                                workflowEditor.move_selected_member_up()
                                        }
                                    }
                                    EditorButton {
                                        text: "Move down"
                                        Layout.fillWidth: true
                                        height: Math.round(48 * CommonStyle.scaleFactor)
                                        enabled: root.selectedStep && root.selectedStep.members
                                                 && root.selectedMemberIndex >= 0
                                                 && root.selectedMemberIndex
                                                    < root.selectedStep.members.length - 1
                                        onClicked: {
                                            if (workflowEditor)
                                                workflowEditor.move_selected_member_down()
                                        }
                                    }
                                }
                            }

                            // Collapsible add-action type chooser
                            ColumnLayout {
                                visible: root.memberAddChooserOpen
                                Layout.fillWidth: true
                                spacing: 6
                                Text {
                                    text: "Choose action type"
                                    color: CommonStyle.textSecondary
                                    font.pixelSize: root.fontSecondary
                                }
                                Repeater {
                                    model: root.memberPaletteModel
                                    delegate: EditorButton {
                                        Layout.fillWidth: true
                                        height: Math.round(48 * CommonStyle.scaleFactor)
                                        text: modelData.label || actionTypeLabel(modelData.type)
                                        onClicked: {
                                            if (workflowEditor)
                                                workflowEditor.add_member(modelData.type)
                                            root.memberAddChooserOpen = false
                                        }
                                    }
                                }
                            }

                            // Edit selected action (params + optional type change)
                            ColumnLayout {
                                visible: !!root.selectedMember && !root.memberAddChooserOpen
                                Layout.fillWidth: true
                                spacing: 8

                                Rectangle {
                                    Layout.fillWidth: true
                                    height: 1
                                    color: CommonStyle.borderDefault
                                    opacity: 0.6
                                }

                                Text {
                                    text: "Edit: " + actionTypeLabel(
                                              root.selectedMember ? root.selectedMember.type : "")
                                    color: CommonStyle.textPrimary
                                    font.bold: true
                                    font.pixelSize: root.fontSecondary
                                    Layout.fillWidth: true
                                    elide: Text.ElideRight
                                }

                                EditorButton {
                                    Layout.fillWidth: true
                                    height: Math.round(48 * CommonStyle.scaleFactor)
                                    text: root.memberTypeChooserOpen ? "Hide types" : "Change type"
                                    onClicked: {
                                        root.memberAddChooserOpen = false
                                        root.memberTypeChooserOpen = !root.memberTypeChooserOpen
                                    }
                                }

                                ColumnLayout {
                                    visible: root.memberTypeChooserOpen
                                    Layout.fillWidth: true
                                    spacing: 6
                                    Repeater {
                                        model: root.memberPaletteModel
                                        delegate: EditorButton {
                                            Layout.fillWidth: true
                                            height: Math.round(48 * CommonStyle.scaleFactor)
                                            text: modelData.label || actionTypeLabel(modelData.type)
                                            accent: root.selectedMember
                                                    && root.selectedMember.type === modelData.type
                                            onClicked: {
                                                if (workflowEditor)
                                                    workflowEditor.set_member_type(modelData.type)
                                                root.memberTypeChooserOpen = false
                                            }
                                        }
                                    }
                                }

                                Repeater {
                                    model: {
                                        if (!root.selectedMember || !workflowEditor)
                                            return []
                                        return workflowEditor.param_fields(root.selectedMember.type || "")
                                    }
                                    delegate: ColumnLayout {
                                        Layout.fillWidth: true
                                        spacing: 4
                                        readonly property string fieldKey: modelData.key || modelData
                                        Text {
                                            text: modelData.label || fieldKey
                                            color: CommonStyle.textSecondary
                                            font.pixelSize: root.fontSecondary
                                        }
                                        TextField {
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: Math.round(52 * CommonStyle.scaleFactor)
                                            readOnly: true
                                            color: CommonStyle.textPrimary
                                            font.pixelSize: root.fontField
                                            font.bold: true
                                            text: {
                                                if (!root.selectedMember || !root.selectedMember.params)
                                                    return ""
                                                var v = root.selectedMember.params[fieldKey]
                                                return v === undefined || v === null ? "" : String(v)
                                            }
                                            background: Rectangle {
                                                color: CommonStyle.backgroundL2
                                                border.color: CommonStyle.borderFocused
                                                radius: 6
                                            }
                                            MouseArea {
                                                anchors.fill: parent
                                                onClicked: {
                                                    numpad.targetField = parent
                                                    numpad.paramKey = fieldKey
                                                    numpad.memberIndex = root.selectedMemberIndex
                                                    numpad.open()
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }

                    // Demoted step tools (distinct from member "who leads")
                    Rectangle {
                        visible: !!root.selectedStep
                        Layout.fillWidth: true
                        height: 1
                        color: CommonStyle.borderDefault
                        opacity: 0.5
                    }

                    Text {
                        visible: !!root.selectedStep
                        text: "This step"
                        color: CommonStyle.textSecondary
                        font.bold: true
                        font.pixelSize: root.fontFloor
                        Layout.fillWidth: true
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        EditorButton {
                            text: "Up"
                            buttonWidth: Math.round(64 * CommonStyle.scaleFactor)
                            height: Math.round(48 * CommonStyle.scaleFactor)
                            enabled: root.selectedIndex > 0
                            onClicked: {
                                if (workflowEditor)
                                    workflowEditor.move_selected_up()
                            }
                        }
                        EditorButton {
                            text: "Down"
                            buttonWidth: Math.round(64 * CommonStyle.scaleFactor)
                            height: Math.round(48 * CommonStyle.scaleFactor)
                            enabled: workflowEditor && root.selectedIndex >= 0
                                     && root.selectedIndex < root.stepsModel.length - 1
                            onClicked: {
                                if (workflowEditor)
                                    workflowEditor.move_selected_down()
                            }
                        }
                        EditorButton {
                            text: "Delete step"
                            Layout.fillWidth: true
                            height: Math.round(48 * CommonStyle.scaleFactor)
                            enabled: root.selectedIndex >= 0
                            onClicked: {
                                if (workflowEditor)
                                    workflowEditor.remove_selected_step()
                            }
                        }
                    }
                }
            }
        }
    }

    SysComponents.NumpadNew {
        id: numpad
        property string paramKey: ""
        property int memberIndex: -1

        onClosed: {
            if (!targetField || paramKey === "" || !workflowEditor)
                return
            var text = targetField.text
            if (text === "" || text === "-" || text === ".")
                return
            var num = Number(text)
            if (isNaN(num))
                return
            if (paramKey === "duration_ms") {
                workflowEditor.set_wait_duration_ms(Math.round(num))
            } else if (memberIndex >= 0) {
                workflowEditor.set_member_param(memberIndex, paramKey, num)
            } else {
                workflowEditor.set_param(paramKey, num)
            }
        }
    }

    // Load popup
    Popup {
        id: loadPopup
        modal: true
        width: Math.round(440 * CommonStyle.scaleFactor)
        height: Math.round(380 * CommonStyle.scaleFactor)
        anchors.centerIn: parent
        background: Rectangle {
            color: CommonStyle.backgroundL1
            radius: 10
            border.color: CommonStyle.borderDefault
        }
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 16
            spacing: 10
            Text {
                text: "Load workflow"
                color: CommonStyle.textPrimary
                font.bold: true
                font.pixelSize: root.fontSection
            }
            ListView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                model: workflowEditor ? workflowEditor.workflow_list : []
                spacing: 6
                delegate: Rectangle {
                    width: ListView.view.width
                    height: Math.round(56 * CommonStyle.scaleFactor)
                    color: loadMouse.containsMouse ? "#3A5A8C" : CommonStyle.backgroundL2
                    radius: 6
                    Text {
                        anchors.centerIn: parent
                        text: modelData
                        color: CommonStyle.textPrimary
                        font.pixelSize: root.fontPrimary
                    }
                    MouseArea {
                        id: loadMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: {
                            if (workflowEditor)
                                workflowEditor.load_document(modelData)
                            loadPopup.close()
                        }
                    }
                }
            }
            EditorButton {
                text: "Cancel"
                Layout.alignment: Qt.AlignRight
                onClicked: loadPopup.close()
            }
        }
    }

    // Full-screen touch keyboard for workflow naming (native IM is disabled)
    TextKeyboardOverlay {
        id: saveAsKeyboard
        title: "Save as"
        placeholderText: "workflow name"
        onAccepted: function(name) {
            if (workflowEditor)
                workflowEditor.save_as(name)
        }
    }

    // Feature-local chrome button. Owns press-linger feedback so every
    // Back/New/Load/Save/palette/Wait-done/Delete control gets the same hit.
    // Accent = selected/primary state (persistent); visuallyPressed = touch flash.
    component EditorButton: Rectangle {
        id: btn
        property string text: ""
        property bool enabled: true
        property bool accent: false
        property int buttonWidth: 0
        property bool visuallyPressed: false
        signal clicked()

        width: buttonWidth > 0 ? buttonWidth : implicitWidth
        implicitWidth: Math.max(Math.round(88 * CommonStyle.scaleFactor), label.implicitWidth + 28)
        height: Math.round(54 * CommonStyle.scaleFactor)
        radius: 8
        opacity: enabled ? 1.0 : 0.45
        color: {
            if (!enabled)
                return CommonStyle.backgroundL2
            // Press flash must read above accent-selected state
            if (visuallyPressed)
                return CommonStyle.buttonPressed
            if (accent)
                return CommonStyle.buttonPrimary
            if (mouse.containsMouse)
                return CommonStyle.cardBackgroundAlt
            return CommonStyle.backgroundL2
        }
        border.color: {
            if (visuallyPressed)
                return CommonStyle.borderFocused
            if (accent)
                return CommonStyle.accentSecondary
            return CommonStyle.borderDefault
        }
        border.width: visuallyPressed ? CommonStyle.borderWidthThick : CommonStyle.borderWidthThin

        Behavior on color {
            ColorAnimation { duration: 60 }
        }

        Text {
            id: label
            anchors.centerIn: parent
            text: btn.text
            color: CommonStyle.textPrimary
            font.pixelSize: root.fontPrimary
            font.bold: accent || btn.visuallyPressed
        }

        MouseArea {
            id: mouse
            anchors.fill: parent
            enabled: btn.enabled
            hoverEnabled: true
            onPressed: btn.visuallyPressed = true
            onCanceled: {
                btn.visuallyPressed = false
                pressLingerTimer.stop()
            }
            onClicked: {
                btn.clicked()
                // Linger so a short finger tap still registers on Steam Deck
                pressLingerTimer.restart()
            }
        }

        Timer {
            id: pressLingerTimer
            interval: 150
            repeat: false
            onTriggered: btn.visuallyPressed = false
        }
    }

    function stepKindBadge(step) {
        if (!step)
            return ""
        if (step.kind === "wait")
            return "WAIT"
        if (step.kind === "parallel")
            return "TOGETHER"
        return (step.type || "ACTION").toString().toUpperCase()
    }

    function actionTypeLabel(typeName) {
        if (!typeName)
            return ""
        var lists = [root.memberPaletteModel, root.paletteModel]
        for (var li = 0; li < lists.length; li++) {
            var list = lists[li]
            if (!list)
                continue
            for (var i = 0; i < list.length; i++) {
                if (list[i] && list[i].type === typeName)
                    return list[i].label || humanizeKey(typeName)
            }
        }
        return humanizeKey(typeName)
    }

    function humanizeKey(key) {
        if (key === undefined || key === null)
            return ""
        var s = String(key).replace(/_/g, " ")
        if (s.length === 0)
            return s
        return s.charAt(0).toUpperCase() + s.slice(1)
    }

    function stepTitle(step) {
        if (!step)
            return ""
        if (step.kind === "wait")
            return "Wait"
        if (step.kind === "parallel")
            return "Parallel group"
        return actionTypeLabel(step.type || step.id || "Action")
    }

    function stepSummary(step) {
        if (!step)
            return ""
        if (step.kind === "wait")
            return (step.duration_ms || 0) + " ms"
        if (step.kind === "parallel") {
            var n = step.members ? step.members.length : 0
            var cont = step.continue === "continue_immediately"
                       ? "next immediately" : "wait until done"
            return n + " start together · " + cont
        }
        var p = step.params || {}
        var parts = []
        for (var k in p)
            parts.push(humanizeKey(k) + " " + p[k])
        var cont2 = step.continue === "continue_immediately" ? "next now" : "wait done"
        return (parts.join(" · ") || "no params") + " · " + cont2
    }

    function memberSummary(member) {
        if (!member)
            return ""
        var p = member.params || {}
        var parts = []
        for (var k in p)
            parts.push(humanizeKey(k) + " " + p[k])
        return parts.join(" · ") || "Tap to edit"
    }

    // Keep loop checkbox in sync when document reloads
    Connections {
        target: workflowEditor
        function onLoop_changed() {
            if (workflowEditor)
                loopBox.checked = workflowEditor.loop
        }
        function onDocument_changed() {
            if (workflowEditor)
                loopBox.checked = workflowEditor.loop
        }
    }

    // Editor-only guide (palette / steps / params) — not shown on video HUD.
    GuideHost {
        id: editorGuideHost
        z: 200
        loaderObjectName: "workflowEditorGuideLoader"
    }
}
