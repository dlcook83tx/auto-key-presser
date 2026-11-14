# Auto Key & Mouse Presser

A simple desktop app that automatically presses keyboard keys and mouse buttons in a sequence you define. You can set delays between actions, choose how long to wait before repeating the whole sequence, and start/stop everything with a hotkey.

## Features

- Build a sequence of keyboard keys and mouse clicks (Left, Right, Middle)
- Set an individual delay (in milliseconds) after each action
- Edit delays directly in the sequence list
- Reorder steps with Up / Down buttons
- Set a repeat interval for the entire sequence
- Configurable global hotkey to Start / Stop (works even when the window is in the background)
- Save and load sequences as external `.json` files
- Remembers your last-used sequence and settings between launches

## Requirements

- Python 3.8 or newer
- Windows, macOS, or Linux

## Installation

1. Install Python from [python.org](https://www.python.org/downloads/) if you don’t already have it.  
   On Windows, check **“Add python.exe to PATH”** during installation.

2. Open a terminal / command prompt and install the required packages:

   ```bash
   pip install customtkinter pynput
   ```

3. Save the script as `auto_key_presser.py` (or any name you like).

## How to Run

```bash
python auto_key_presser.py
```

On Windows you can also double-click the `.py` file if Python is associated with it.

## How to Use

1. **Add an action**
   - Choose **Key** or **Mouse** from the dropdown.
   - For keys: type the key name (`a`, `space`, `enter`, `f1`, `tab`, `esc`, etc.).
   - For mouse: select Left Click, Right Click, or Middle Click.
   - Set the delay in milliseconds, then click **Add**.

2. **Edit a delay**  
   Click inside any delay box in the list, change the number, then press Enter or click outside the box.

3. **Reorder steps**  
   Use the **↑** and **↓** buttons on each row.

4. **Set the repeat interval**  
   This is how long the app waits after finishing the sequence before starting it again.

5. **Change the hotkey** (optional)  
   Default is `F9`. Type a new hotkey (examples: `<f8>`, `<ctrl>+<shift>+a`) and click **Apply Hotkey**.

6. **Start / Stop**
   - Click the **Start** or **Stop** buttons, or
   - Press your hotkey (works even when the window is minimized or not focused).

7. **Save / Load sequences**
   - **Save Sequence** — saves the current sequence and repeat interval to a `.json` file.
   - **Load Sequence** — loads a previously saved `.json` file.

## Supported Keys

Common examples:
- Letters and numbers: `a`, `b`, `1`, `2`
- Special keys: `space`, `enter`, `tab`, `esc`, `backspace`, `delete`
- Arrow keys: `up`, `down`, `left`, `right`
- Function keys: `f1` through `f12`
- Modifiers: `shift`, `ctrl`, `alt`

## Notes

- The first time you run the app, Windows Defender or antivirus software may warn you because the program can control the keyboard and mouse. This is normal — you can allow it.
- If the global hotkey doesn’t work, try running the app as Administrator (right-click → Run as administrator).
- Your last sequence and settings are automatically saved to `auto_key_config.json` in the same folder as the script.

## License

Free to use and modify for personal purposes.
