import pyautogui, time
from PIL import ImageGrab
from collections import defaultdict, deque

pyautogui.FAILSAFE = True

# --- Game board configuration ---
board_x, board_y = 302, 209
tile_w, tile_h   = 32, 32
cols, rows       = 30, 16
reset_x, reset_y = 447, 165
lose_x, lose_y   = 439, 166
win_x, win_y     = 447, 151

# --- Colours ---
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
    """Deterministic propagation: classic two rules."""
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

                    n_val = int(val)
                    # Rule 1: all hidden must be bombs
                    if len(flags) + len(hidden) == n_val and hidden:
                        for nr, nc in hidden:
                            if grid[nr][nc] != '*':
                                grid[nr][nc] = '*'
                                changed = True
                    # Rule 2: all hidden must be safe
                    elif len(flags) == n_val and hidden:
                        for nr, nc in hidden:
                            if grid[nr][nc] != '0':
                                grid[nr][nc] = '0'
                                changed = True
    return grid

def read_board(img):
    pix = img.load()
    grid = []
    for r in range(rows):
        row = []
        for c in range(cols):
            tl_x = board_x + c * tile_w
            tl_y = board_y + r * tile_h
            tl = pix[tl_x, tl_y]

            if tl == WHITE:
                # unopened/flag detection via a probe pixel near bottom
                probe = pix[tl_x + 17, tl_y + tile_h - 9]
                row.append('*' if probe == BLACK else '-')
            else:
                cx = tl_x + tile_w // 2
                cy = tl_y + tile_h // 2
                row.append(COLOUR_MAP.get(pix[cx, cy], '0'))
        grid.append(row)
    return grid

def pixel(img, x, y):
    return img.load()[x, y]

# ======== Exact probability solver over the border ========

def build_constraints(grid):
    """
    Build linear constraints for the border:
    For each numbered cell N with H hidden neighbors and F flagged neighbors:
        sum(x_h for h in H) == N - F
    Returns:
        vars_set: set of (r,c) hidden border cells
        constraints: list of (tuple(hidden_cells), remaining_bombs)
    """
    constraints = []
    vars_set = set()

    for r in range(rows):
        for c in range(cols):
            val = grid[r][c]
            if val.isdigit() and val != '0':
                neighs = list(neighbors(r, c))
                hidden = [(nr, nc) for nr, nc in neighs if grid[nr][nc] == '-']
                flags  = [(nr, nc) for nr, nc in neighs if grid[nr][nc] == '*']
                remaining = int(val) - len(flags)
                if hidden:
                    constraints.append((tuple(hidden), remaining))
                    vars_set.update(hidden)
    return vars_set, constraints

def split_components(vars_set, constraints):
    """
    Split the border into independent components (variables that co-occur in any constraint).
    Returns list of (vars_list, constraints_subset).
    """
    # Build adjacency among vars: edge if two vars appear in the same constraint
    adj = defaultdict(set)
    for hidden_cells, _ in constraints:
        hc = list(hidden_cells)
        for i in range(len(hc)):
            for j in range(i+1, len(hc)):
                a, b = hc[i], hc[j]
                adj[a].add(b)
                adj[b].add(a)

    # BFS over vars to get components
    unvisited = set(vars_set)
    components = []
    # index constraints per var for quick subsetting
    cons_per_var = defaultdict(list)
    for idx, (hc, rem) in enumerate(constraints):
        for v in hc:
            cons_per_var[v].append(idx)

    while unvisited:
        start = unvisited.pop()
        comp_vars = {start}
        q = deque([start])
        while q:
            v = q.popleft()
            for u in adj[v]:
                if u in unvisited:
                    unvisited.remove(u)
                    comp_vars.add(u)
                    q.append(u)
        # collect constraints that touch comp_vars
        comp_cons_idx = set()
        for v in comp_vars:
            comp_cons_idx.update(cons_per_var[v])
        comp_constraints = [constraints[i] for i in sorted(comp_cons_idx)]
        components.append((sorted(list(comp_vars)), comp_constraints))
    return components

def exact_component_probabilities(comp_vars, comp_constraints, max_enum_vars=22, max_solutions=200000):
    """
    Enumerate all satisfying assignments for this component (if small enough).
    Returns:
        prob dict for comp_vars: P(var is a mine)
        solved_exactly: bool
    If too large, falls back to guided Monte Carlo sampling under constraints.
    """
    n = len(comp_vars)
    index = {v: i for i, v in enumerate(comp_vars)}

    # rewrite constraints in index space
    cons = []
    for hidden_cells, rem in comp_constraints:
        idxs = [index[v] for v in hidden_cells if v in index]
        if not idxs:
            # constraint only touched other components or has become fully satisfied; skip
            continue
        cons.append((idxs, rem))

    # Pre-check feasibility quickly
    for idxs, rem in cons:
        if rem < 0 or rem > len(idxs):
            return {v: 0.5 for v in comp_vars}, False  # inconsistent read; neutral fallback

    # Variable ordering heuristic: most constrained first
    deg = [0]*n
    for idxs, _ in cons:
        for i in idxs:
            deg[i] += 1
    order = sorted(range(n), key=lambda i: -deg[i])

    # Constraint tracking structures
    cons_idxs = [list(idxs) for idxs, _ in cons]
    cons_need = [rem for _, rem in cons]
    cons_unassigned = [len(idxs) for idxs in cons_idxs]

    assign = [-1]*n  # -1 unknown, 0 safe, 1 mine
    mine_counts = [0]*n
    total_solutions = 0

    # Early pruning helpers
    var_to_cons = [[] for _ in range(n)]
    for ci, idxs in enumerate(cons_idxs):
        for vi in idxs:
            var_to_cons[vi].append(ci)

    def propagate_check(ci):
        # Bounds: 0 <= cons_need[ci] <= cons_unassigned[ci]
        return 0 <= cons_need[ci] <= cons_unassigned[ci]

    def dfs(pos, nodes_left=[2_000_000], sols_cap=[max_solutions]):
        nonlocal total_solutions
        if sols_cap[0] <= 0 or nodes_left[0] <= 0:
            return
        if pos == n:
            total_solutions += 1
            for i in range(n):
                if assign[i] == 1:
                    mine_counts[i] += 1
            sols_cap[0] -= 1
            return

        vi = order[pos]

        # Try value 0 then 1; pick the more promising first using a tiny heuristic:
        # prefer the value that violates fewer minimums immediately
        trials = [0, 1]

        for val in trials:
            assign[vi] = val
            changed = []
            ok = True
            # update constraints
            for ci in var_to_cons[vi]:
                cons_unassigned[ci] -= 1
                if val == 1:
                    cons_need[ci] -= 1
                changed.append(ci)
                if not propagate_check(ci):
                    ok = False
                    break
            if ok:
                nodes_left[0] -= 1
                dfs(pos+1, nodes_left, sols_cap)

            # undo
            for ci in changed:
                if val == 1:
                    cons_need[ci] += 1
                cons_unassigned[ci] += 1
            assign[vi] = -1

    if n <= max_enum_vars:
        dfs(0)
        if total_solutions > 0:
            return {comp_vars[i]: mine_counts[i]/total_solutions for i in range(n)}, True

    # Fallback: guided Monte Carlo under constraints (randomized backtracking)
    import random
    samples_target = 5000
    success = 0
    mine_counts = [0]*n

    def randomized_backtrack():
        nonlocal success
        # reset
        for i in range(n):
            assign[i] = -1
        for ci in range(len(cons_need)):
            cons_need[ci] = cons[ci][1]
            cons_unassigned[ci] = len(cons[ci][0])

        order_rand = order[:]  # keep good heuristic ordering
        # randomized values per step
        def step(pos):
            if pos == n:
                return True
            vi = order_rand[pos]
            # compute a soft bias from constraints touching vi
            total_need = 0
            total_unassigned = 0
            for ci in var_to_cons[vi]:
                total_need += cons_need[ci]
                total_unassigned += cons_unassigned[ci]
            # basic bias: if many mines still needed, increase chance of 1
            p1 = 0.0 if total_unassigned == 0 else min(0.9, max(0.1, total_need / max(1, total_unassigned)))
            for val in (1 if random.random() < p1 else 0, 0 if random.random() < p1 else 1):
                assign[vi] = val
                changed = []
                ok = True
                for ci in var_to_cons[vi]:
                    cons_unassigned[ci] -= 1
                    if val == 1:
                        cons_need[ci] -= 1
                    changed.append(ci)
                    if not (0 <= cons_need[ci] <= cons_unassigned[ci]):
                        ok = False
                        break
                if ok and step(pos+1):
                    return True
                for ci in changed:
                    if val == 1:
                        cons_need[ci] += 1
                    cons_unassigned[ci] += 1
                assign[vi] = -1
            return False

        if step(0):
            success += 1
            for i in range(n):
                if assign[i] == 1:
                    mine_counts[i] += 1
            return True
        return False

    attempts = 0
    while success < samples_target and attempts < samples_target * 10:
        attempts += 1
        randomized_backtrack()

    if success > 0:
        return {comp_vars[i]: mine_counts[i]/success for i in range(n)}, False

    # last resort neutral
    return {v: 0.5 for v in comp_vars}, False

def compute_probabilities_exact(grid):
    """
    Compute P(mine) for each hidden cell:
    - exact enumeration per independent border component
    - cells not on the border default to 0.5 (no info)
    """
    vars_set, constraints = build_constraints(grid)
    probs = defaultdict(lambda: 0.5)

    if not vars_set:
        # No border info at all; leave defaults
        return probs

    components = split_components(vars_set, constraints)
    for comp_vars, comp_constraints in components:
        comp_probs, solved_exactly = exact_component_probabilities(comp_vars, comp_constraints)
        probs.update(comp_probs)

    return probs

# ===================== Main loop =====================

time.sleep(1)

while True:
    img = ImageGrab.grab(all_screens=True)

    # End-of-game checks
    if pixel(img, win_x, win_y) == (0, 0, 0):
        print("We won!")
        break
    if pixel(img, lose_x, lose_y) == (0, 0, 0):
        print("We lost!")
        break

    grid = read_board(img)
    old_grid = [row[:] for row in grid]
    grid = apply_rules(grid)

    actions_done = 0
    # Apply deterministic moves (already encoded in grid changes)
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

    # If no certain moves, use exact probabilities
    if actions_done == 0:
        # Compute exact P(mine) over border
        probs = compute_probabilities_exact(grid)

        # Any guaranteed safes / mines?
        sure_safes = [(r, c) for r in range(rows) for c in range(cols)
                      if grid[r][c] == '-' and probs[(r, c)] == 0.0]
        sure_mines = [(r, c) for r in range(rows) for c in range(cols)
                      if grid[r][c] == '-' and probs[(r, c)] == 1.0]

        # Prefer acting on certainties first
        acted = False
        for r, c in sure_mines:
            x = board_x + c * tile_w + tile_w // 2
            y = board_y + r * tile_h + tile_h // 2
            pyautogui.rightClick(x, y)
            acted = True
        for r, c in sure_safes:
            x = board_x + c * tile_w + tile_w // 2
            y = board_y + r * tile_h + tile_h // 2
            pyautogui.click(x, y)
            acted = True

        if not acted:
            # pick the hidden cell with minimal P(mine)
            hidden = [(r, c) for r in range(rows) for c in range(cols) if grid[r][c] == '-']
            if hidden:
                best_cell = min(hidden, key=lambda cell: probs[cell])
                r, c = best_cell
                x = board_x + c * tile_w + tile_w // 2
                y = board_y + r * tile_h + tile_h // 2
                print(f"Guessing at {best_cell} with exact/MC P(bomb)={probs[best_cell]:.4f}")
                pyautogui.click(x, y)

    time.sleep(0.03)  # refresh a bit slower to let UI update
