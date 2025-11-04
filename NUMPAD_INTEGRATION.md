# Numpad Integration for CommandTab

## Summary
Added a comprehensive numpad feature to your CommandTab that allows you to enter numbers (including floats and negative numbers) without a keyboard.

## Changes Made

### 1. **Created NumpadNew.qml** (`qml/components/NumpadNew.qml`)
   - Enhanced numpad popup component with support for:
     - Basic digits (0-9)
     - Decimal point (.)
     - Negative sign toggle (−)
     - Backspace/Delete (←)
     - Clear button
     - Confirm button (✓)
   - Features:
     - Display area showing current input
     - Prevents multiple decimal points
     - Smart negative sign handling (can toggle at any point)
     - Properly formatted with your app's color scheme
     - 4-column layout for better UX

### 2. **Created NumpadButton.qml** (`qml/components/NumpadButton.qml`)
   - Reusable button component for numpad
   - Supports normal and special buttons (different styling)
   - Smooth color animations on press

### 3. **Updated CommandTab.qml** (`qml/overlays/CommandTab.qml`)
   - Integrated NumpadNew component
   - Modified number input fields to:
     - Show a numpad button (🔢) inside each input field
     - Auto-open numpad when field is focused
     - Allow manual click on the numpad button
   - Updated validator to accept float and negative numbers: `/^-?\d*\.?\d*$/`
   - Improved visual feedback with color transitions

## How to Use

1. **Auto-trigger**: Click on any number input field and the numpad will automatically pop up
2. **Manual trigger**: Click the 🔢 button inside the input field to open the numpad
3. **Enter numbers**:
   - Tap digit buttons (0-9) to enter numbers
   - Tap `.` to add decimal point (automatically prepends "0." if needed)
   - Tap `−` to toggle negative sign
   - Tap `←` to delete the last character
   - Tap `Clear` to clear the entire input
   - Tap `✓` to confirm and close the numpad

## Features

✅ Float numbers (e.g., 3.14, -2.5)
✅ Negative numbers (e.g., -100, -0.5)
✅ Integer numbers (e.g., 42, -7)
✅ Smart decimal point handling
✅ Backspace functionality
✅ Display shows current input
✅ Matches your app's dark theme color scheme
✅ Smooth animations and transitions
✅ Touch-friendly button sizes

## Technical Details

- Uses `RegExpValidator` with pattern `/^-?\d*\.?\d*$/` to validate input
- Numpad closes when confirm button is pressed
- Input field loses focus after numpad closes
- Each number input field in CommandTab has independent numpad access
- Display area in numpad shows real-time value as you type

## Files Modified/Created
- ✨ Created: `qml/components/NumpadNew.qml`
- ✨ Created: `qml/components/NumpadButton.qml`
- 🔄 Modified: `qml/overlays/CommandTab.qml`

Note: The old `Numpad.qml` component is still available if needed for other purposes.
