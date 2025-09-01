import pyautogui, random, time
import ctypes

pyautogui.FAILSAFE = True

board_x, board_y = 302, 209
box_w, box_h = 32, 32
rows, cols = 9, 9
duration = 4
reset_x, reset_y = 447, 165
lose_x, lose_y = 439, 166
win_x, win_y = 447, 151

def pixel(x, y):
    hdc = ctypes.windll.user32.GetDC(0)
    c = ctypes.windll.gdi32.GetPixel(hdc, x, y)
    ctypes.windll.user32.ReleaseDC(0, hdc)
    r, g, b = c & 0xff, (c >> 8) & 0xff, (c >> 16) & 0xff
    return (r, g, b)

time.sleep(2)

while True:
    if pixel(win_x, win_y) == (0, 0, 0):
        break
    end = time.time() + duration
    while time.time() < end:
        if pixel(lose_x, lose_y) == (0, 0, 0) or pixel(win_x, win_y) == (0, 0, 0):
            break
        c = random.randint(0, cols - 1)
        r = random.randint(0, rows - 1)
        x = board_x + c * box_w + box_w // 2
        y = board_y + r * box_h + box_h // 2
        pyautogui.click(x, y)
    pyautogui.click(reset_x, reset_y)