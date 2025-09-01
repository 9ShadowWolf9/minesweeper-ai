import pyautogui, time
from PIL import ImageGrab
import random
pyautogui.FAILSAFE = True


board_x, board_y = 302, 209
tile_w, tile_h   = 32, 32
cols, rows       = 9, 9
reset_x, reset_y = 447, 165
lose_x, lose_y   = 439, 166
win_x, win_y     = 447, 151

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
COLOUR_MAP = {
    (0, 0, 255): '1',
    (0, 123, 0): '2',
    (255, 0, 0): '3',
    (0, 0, 123): '4',
    (123, 0, 0): '5',
    (0, 123, 123): '6',
    (123, 123, 123): '8',
}


def neighbors(r, c):
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == dc == 0:
                continue
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                yield nr, nc

def apply_rules(grid):
    changed = True
    while changed:
        changed = False
        for r in range(rows):
            for c in range(cols):
                val = grid[r][c]
                if val.isdigit() and val != '0':
                    neighs = list(neighbors(r, c))
                    flags  = [(nr, nc) for nr, nc in neighs if grid[nr][nc] == '*']
                    hidden = [(nr, nc) for nr, nc in neighs if grid[nr][nc] == '-']

                    # Rule 1 – must be bombs
                    if len(flags) + len(hidden) == int(val) and hidden:
                        for nr, nc in hidden:
                            grid[nr][nc] = '*'
                            changed = True

                    # Rule 2 – must be safe
                    if len(flags) == int(val) and hidden:
                        for nr, nc in hidden:
                            grid[nr][nc] = '0'
                            changed = True
    return grid

def read_board():
    img = ImageGrab.grab(all_screens=True)
    grid = []
    for r in range(rows):
        row = []
        for c in range(cols):
            tl_x = board_x + c * tile_w
            tl_y = board_y + r * tile_h
            tl = img.getpixel((tl_x, tl_y))

            if tl == WHITE:
                probe = img.getpixel((tl_x + 17, tl_y + tile_h - 1 - 8))
                row.append('*' if probe == BLACK else '-')
            else:
                cx = tl_x + tile_w // 2
                cy = tl_y + tile_h // 2
                row.append(COLOUR_MAP.get(img.getpixel((cx, cy)), '0'))
        grid.append(row)
    return grid

def pixel(x, y):
    return ImageGrab.grab(all_screens=True).getpixel((x, y))


time.sleep(2)

while True:
    # End-of-game checks
    if pixel(win_x, win_y) == (0, 0, 0):
        print("We won!")
        break
    if pixel(lose_x, lose_y) == (0, 0, 0):
        print("We lost!")
        break

    grid = read_board()

    old_grid = [row[:] for row in grid]
    grid = apply_rules(grid)

    actions_done = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] != old_grid[r][c]:
                x = board_x + c * tile_w + tile_w // 2
                y = board_y + r * tile_h + tile_h // 2
                if grid[r][c] == '*':
                    pyautogui.rightClick(x, y)
                elif grid[r][c] == '0':
                    pyautogui.click(x, y)
                actions_done += 1

    if actions_done == 0:
        hidden = [(r, c) for r in range(rows) for c in range(cols)
                  if grid[r][c] == '-']
        if hidden:
            r, c = random.choice(hidden)
            x = board_x + c * tile_w + tile_w // 2
            y = board_y + r * tile_h + tile_h // 2
            pyautogui.click(x, y)
            time.sleep(0.1)

    time.sleep(0.1)