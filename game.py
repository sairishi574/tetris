import asyncio, random
from js import document
from pyodide.ffi import create_proxy

# Linked List Implementation
class Node:
    def __init__(self, value):
        self.value = value
        self.next = None

class LinkedList:
    def __init__(self):
        self.head = None
        self.tail = None
        self._size = 0

    def append(self, value):
        n = Node(value)
        if not self.head:
            self.head = self.tail = n
        else:
            self.tail.next = n
            self.tail = n
        self._size += 1

    def popleft(self):
        if not self.head: return None
        v = self.head.value
        self.head = self.head.next
        if not self.head:
            self.tail = None
        self._size -= 1
        return v

    def __iter__(self):
        cur = self.head
        while cur:
            yield cur.value
            cur = cur.next

    def map_inplace(self, fn):
        cur = self.head
        while cur:
            cur.value = fn(cur.value)
            cur = cur.next

    def clear(self):
        self.head = self.tail = None
        self._size = 0

    def __len__(self):
        return self._size


# Setup canvas
canvas = document.getElementById("game")
ctx = canvas.getContext("2d")
COLS, ROWS = 10, 20
CELL = 30

COLORS = {
    "I": "#6ee7ff",
    "O": "#fde047",
    "T": "#c084fc",
    "S": "#34d399",
    "Z": "#fb7185",
    "J": "#93c5fd",
    "L": "#fbbf24",
}
SHAPES = {
    "I": [(0,1),(1,1),(2,1),(3,1)],
    "O": [(1,0),(2,0),(1,1),(2,1)],
    "T": [(1,0),(0,1),(1,1),(2,1)],
    "S": [(1,1),(2,1),(0,2),(1,2)],
    "Z": [(0,1),(1,1),(1,2),(2,2)],
    "J": [(0,0),(0,1),(1,1),(2,1)],
    "L": [(2,0),(0,1),(1,1),(2,1)],
}

# Globals
board = [[None for _ in range(COLS)] for _ in range(ROWS)]
current = LinkedList()
current_name = None
current_color = None
pivot = (0,0)
queue = LinkedList()
score = 0
game_running = False
paused = False
game_task = None

def bag7():
    names = list(SHAPES.keys())
    random.shuffle(names)
    return names

def ensure_queue():
    global queue
    if len(queue) < 7:
        for name in bag7():
            queue.append(name)

def spawn_new():
    global current, current_name, current_color, pivot
    ensure_queue()
    name = queue.popleft()
    current_name = name
    current_color = COLORS[name]
    startx, starty = 3, 0
    current.clear()
    for (dx, dy) in SHAPES[name]:
        current.append((startx + dx, starty + dy))
    pivot = list(current)[1]

def collides(coords):
    for (x, y) in coords:
        if x < 0 or x >= COLS or y >= ROWS:
            return True
        if y >= 0 and board[y][x]:
            return True
    return False

def move(dx, dy):
    trial = [(x+dx, y+dy) for (x,y) in current]
    if not collides(trial):
        current.map_inplace(lambda p: (p[0]+dx, p[1]+dy))
        return True
    return False

def rotate():
    global current, pivot
    if current_name == "O": return
    px, py = pivot
    trial = []
    for (x,y) in current:
        nx = px - (y - py)
        ny = py + (x - px)
        trial.append((nx, ny))
    if not collides(trial):
        it = iter(trial)
        current.map_inplace(lambda _: next(it))

def lock_piece():
    global score
    for (x,y) in current:
        if 0 <= y < ROWS:
            board[y][x] = current_color
    spawn_new()

def draw_cell(x, y, color):
    ctx.fillStyle = color
    ctx.fillRect(x*CELL+1, y*CELL+1, CELL-2, CELL-2)

def draw():
    ctx.fillStyle = "#0b0f25"
    ctx.fillRect(0,0,COLS*CELL,ROWS*CELL)
    for y in range(ROWS):
        for x in range(COLS):
            if board[y][x]:
                draw_cell(x,y,board[y][x])
    for (x,y) in current:
        if y>=0: draw_cell(x,y,current_color)

async def game_loop():
    global game_running
    while game_running:
        if not paused:
            if not move(0,1):
                lock_piece()
            draw()
        await asyncio.sleep(0.5)

# --- NEW: Start Game Button Handler ---
def start_game(event=None):
    global board, queue, score, game_running, game_task, paused
    # Reset everything
    board = [[None for _ in range(COLS)] for _ in range(ROWS)]
    queue.clear()
    score = 0
    paused = False
    document.getElementById("score").innerText = "0"
    game_running = True

    spawn_new()
    draw()

    # Start async loop
    game_task = asyncio.create_task(game_loop())
