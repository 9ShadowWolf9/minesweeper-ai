# 🕹️ Minesweeper Bot

Automated Minesweeper solver and random clicker using Python and image recognition.

---

## 📝 Overview

This repository contains scripts to interact with a Minesweeper game on Windows:

- **`main.py`** – Smart solver using basic Minesweeper deduction rules.
- **`randombot.py`** – Random tile clicker bot.
- **`analyzer.py`** – Reads the Minesweeper board and prints it to the console for debugging and visualization.
- **`probability_bot.py`** – Concept of bot with integrated math probability (in development).

The bots use **PyAutoGUI** for mouse control and **Pillow** for screen capture.

---

## ⚡ Features

- Detects the Minesweeper board from the screen.
- Reads tile values using pixel color mapping.
- Applies deduction rules to flag bombs and reveal safe tiles.
- Automatically clicks or flags tiles.
- Random clicker mode for testing or experimentation.
- Detects end-of-game (win/loss).
---

## 🛠️ Requirements

All dependencies are listed in the `requirements.txt` file in the main folder.

Install them with:

```bash
pip install -r requirements.txt
```

---

## 🚀 Usage

1. Open Minesweeper and make sure the window is fully visible.
2. Adjust board coordinates in scripts if needed:

```python
board_x, board_y = 302, 209
```
3. Run the script you want:
```
python main.py       # Smart solver
python randombot.py  # Random clicker
python analyzer.py   # Board analyzer
```
4. Watch the bot play Minesweeper automatically! 🎯

---

## 🤖 How It Works
1. Board Reading – Captures the screen and identifies tiles using pixel colors.
2. Logic Application (main.py):
   - Rule 1: If the number of hidden tiles + flags equals the number on a tile → mark hidden tiles as bombs.
   - Rule 2: If the number of flags equals the number on a tile → mark remaining neighbors as safe.
3. Actions – Clicks safe tiles and flags bombs using PyAutoGUI.
4. Random Clicker – randombot.py clicks random tiles for casual play or testing.

---

## ⚠️ Notes
 - Make sure display scale is 100% for accurate pixel detection.
 - May not work correctly with custom Minesweeper skins or tile sizes.
 - Use responsibly — avoid automated play in competitive or online versions.
