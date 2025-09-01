from PIL import ImageGrab

board_x, board_y = 302, 209
tile_w, tile_h   = 32, 32
cols, rows       = 9, 9
WHITE            = (255, 255, 255)
BLACK            = (0, 0, 0)

COLOUR_MAP = {
    (0, 0, 255):   '1',
    (0, 123, 0):   '2',
    (255, 0, 0):   '3',
    (0, 0, 123):   '4',
    (123, 0, 0):   '5',
    (0, 123, 123): '6',
    (123, 123, 123): '8',
}

img = ImageGrab.grab(all_screens=True)

grid = []
for r in range(rows):
    row = []
    for c in range(cols):
        tl_x = board_x + c * tile_w
        tl_y = board_y + r * tile_h
        tl = img.getpixel((tl_x, tl_y))

        if tl == WHITE:  # unclicked
            probe = img.getpixel((tl_x + 17, tl_y + tile_h - 1 - 8))
            row.append('*' if probe == BLACK else '-')
        else:            # clicked (empty or number)
            cx = tl_x + tile_w // 2
            cy = tl_y + tile_h // 2
            row.append(COLOUR_MAP.get(img.getpixel((cx, cy)), '0'))
    grid.append(row)

# framed output
top    = '┌' + '─' * (2 * cols) + '┐'
bottom = '└' + '─' * (2 * cols) + '┘'
print(top)
for row in grid:
    print('│ ' + ' '.join(row) + ' │')
print(bottom)