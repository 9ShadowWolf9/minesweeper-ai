# 🕹️ Minesweeper Bot

Automated Minesweeper solver and random clicker using Python and image recognition.

---

## 📝 Overview

This repository contains scripts to interact with a Minesweeper game on Windows:

- **`main.py`** – Smart solver using basic Minesweeper deduction rules.
- **`randombot.py`** – Random tile clicker bot.
- **`analyzer.py`** – Reads the Minesweeper board and prints it to the console for debugging/visualization.

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
