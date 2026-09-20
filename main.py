import tkinter as tk
from tkinter import ttk, messagebox
from collections import deque
from dataclasses import dataclass, field
from typing import Optional, Callable
import math
import time


# =========================================================
# ТИПИ ДАНИХ
# =========================================================

VertexPositions = dict[int, tuple[int, int]]
ConnectionList = list[tuple[int, int]]
AdjacencyList = dict[int, list[int]]


@dataclass
class BFSResult:
    path: Optional[list[int]]
    search_order: list[int]
    queue_states: list[list[int]]
    iterations: int


@dataclass
class AnimationData:
    path: Optional[list[int]] = None
    search_order: list[int] = field(default_factory=list)
    queue_states: list[list[int]] = field(default_factory=list)
    step: int = 0
    opened: set[int] = field(default_factory=set)
    algorithm_time: float = 0.0
    paused: bool = False
    running: bool = False
    after_id: Optional[str] = None


# =========================================================
# ГОЛОВНЕ ВІКНО
# =========================================================

root = tk.Tk()
root.title("Дослідження алгоритму пошуку в ширину (BFS)")
root.geometry("1250x780")
root.minsize(1050, 680)

title_label = ttk.Label(
    root,
    text="ДОСЛІДЖЕННЯ АЛГОРИТМУ ПОШУКУ В ШИРИНУ (BFS)",
    font=("Arial", 16, "bold")
)
title_label.pack(pady=10)

main_frame = ttk.Frame(root)
main_frame.pack(fill="both", expand=True, padx=10, pady=5)


# =========================================================
# ЛІВА ЧАСТИНА — ГРАФ
# =========================================================

graph_frame = ttk.LabelFrame(main_frame, text="Граф")
graph_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

canvas = tk.Canvas(graph_frame, bg="white", highlightthickness=0)
canvas.pack(fill="both", expand=True, padx=5, pady=5)


# =========================================================
# ПРАВА ЧАСТИНА — КЕРУВАННЯ
# =========================================================

control_frame = ttk.LabelFrame(main_frame, text="Керування", width=340)
control_frame.pack(side="right", fill="y", padx=(5, 0))
control_frame.pack_propagate(False)

notebook = ttk.Notebook(control_frame)
notebook.pack(fill="both", expand=True, padx=5, pady=5)


def create_scrollable_tab(
        notebook_widget: ttk.Notebook,
        title: str
) -> ttk.Frame:
    tab_container = ttk.Frame(notebook_widget)
    tab_container.columnconfigure(0, weight=1)
    tab_container.rowconfigure(0, weight=1)

    tab_canvas = tk.Canvas(tab_container, highlightthickness=0)
    scrollbar = ttk.Scrollbar(
        tab_container,
        orient="vertical",
        command=tab_canvas.yview
    )

    tab_canvas.configure(
        yscrollcommand=scrollbar.set,
        yscrollincrement=20
    )

    tab_canvas.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")

    content_frame = ttk.Frame(tab_canvas)
    content_window = tab_canvas.create_window(
        (0, 0),
        window=content_frame,
        anchor="nw"
    )

    def update_scroll_region(_event: object = None) -> None:
        tab_canvas.configure(scrollregion=tab_canvas.bbox("all"))

    def resize_content(event: tk.Event) -> None:
        tab_canvas.itemconfigure(content_window, width=event.width)

    def on_mousewheel(event: tk.Event) -> None:
        tab_canvas.yview_scroll(int(-event.delta / 120), "units")

    def bind_mousewheel(_event: object = None) -> None:
        tab_canvas.bind_all("<MouseWheel>", on_mousewheel)

    def unbind_mousewheel(_event: object = None) -> None:
        tab_canvas.unbind_all("<MouseWheel>")

    content_frame.bind("<Configure>", update_scroll_region)
    tab_canvas.bind("<Configure>", resize_content)
    tab_container.bind("<Enter>", bind_mousewheel)
    tab_container.bind("<Leave>", unbind_mousewheel)

    notebook_widget.add(tab_container, text=title)
    return content_frame


search_tab = create_scrollable_tab(notebook, "Пошук BFS")
edit_tab = create_scrollable_tab(notebook, "Редагування графа")


# =========================================================
# НИЖНЯ ОБЛАСТЬ — РЕЗУЛЬТАТИ
# =========================================================

status_frame = ttk.LabelFrame(root, text="Хід та результати пошуку")
status_frame.pack(fill="x", padx=10, pady=(5, 10))

status_label = ttk.Label(
    status_frame,
    text="Програма готова до роботи.",
    justify="left"
)
status_label.pack(anchor="w", padx=10, pady=8)


# =========================================================
# ФІКСОВАНІ КООРДИНАТИ
# =========================================================

normal_vertices: VertexPositions = {
    1: (80, 300),
    2: (200, 80), 3: (200, 190), 4: (200, 300),
    5: (200, 410), 6: (200, 520),
    7: (350, 60), 8: (350, 130), 9: (350, 210),
    10: (350, 280), 11: (350, 350), 12: (350, 430),
    13: (350, 510),
    14: (500, 50), 15: (500, 120), 16: (500, 190),
    17: (500, 260), 18: (500, 330), 19: (500, 400),
    20: (500, 470), 21: (500, 540),
    22: (650, 80), 23: (650, 160), 24: (650, 240),
    25: (650, 320), 26: (650, 400), 27: (650, 480),
    28: (800, 170), 29: (800, 300), 30: (800, 430)
}

tree_vertices: VertexPositions = {
    1: (440, 60),
    2: (100, 190), 3: (270, 190), 4: (440, 190),
    5: (610, 190), 6: (780, 190),
    7: (60, 330), 8: (140, 330),
    9: (230, 330), 10: (310, 330),
    11: (400, 330), 12: (480, 330),
    13: (570, 330), 14: (650, 330),
    15: (740, 330), 16: (820, 330),
    17: (40, 500), 18: (100, 500), 19: (160, 500),
    20: (220, 500), 21: (280, 500), 22: (340, 500),
    23: (400, 500), 24: (460, 500), 25: (520, 500),
    26: (580, 500), 27: (640, 500), 28: (700, 500),
    29: (760, 500), 30: (820, 500)
}


# =========================================================
# ПОЧАТКОВІ СТРУКТУРИ
# =========================================================

normal_edges: ConnectionList = [
    (1, 2), (1, 3), (1, 4), (1, 5), (1, 6),
    (2, 7), (2, 8),
    (3, 8), (3, 9),
    (4, 9), (4, 10), (4, 11),
    (5, 11), (5, 12),
    (6, 12), (6, 13),
    (7, 14), (8, 14), (8, 15),
    (9, 15), (9, 16),
    (10, 16), (10, 17),
    (11, 17), (11, 18),
    (12, 18), (12, 19),
    (13, 19), (13, 20), (13, 21),
    (14, 22), (15, 22), (15, 23),
    (16, 23), (16, 24),
    (17, 24), (17, 25),
    (18, 25), (18, 26),
    (19, 26), (19, 27),
    (20, 27), (21, 27),
    (22, 28), (23, 28),
    (24, 28), (24, 29),
    (25, 29),
    (26, 29), (26, 30),
    (27, 30)
]

directed_arcs_initial: ConnectionList = normal_edges.copy()

tree_edges: ConnectionList = [
    (1, 2), (1, 3), (1, 4), (1, 5), (1, 6),
    (2, 7), (2, 8),
    (3, 9), (3, 10),
    (4, 11), (4, 12),
    (5, 13), (5, 14),
    (6, 15), (6, 16),
    (7, 17), (7, 18),
    (8, 19), (8, 20),
    (9, 21), (9, 22),
    (10, 23), (10, 24),
    (11, 25), (11, 26),
    (12, 27), (12, 28),
    (13, 29), (13, 30)
]


# =========================================================
# ПОТОЧНИЙ СТАН ГРАФА
# =========================================================

vertices: VertexPositions = normal_vertices.copy()
undirected_edges: ConnectionList = normal_edges.copy()
directed_arcs: ConnectionList = []
graph_type: str = "normal"

animation_data = AnimationData()


# =========================================================
# ДОПОМІЖНІ ФУНКЦІЇ СТРУКТУРИ
# =========================================================

def graph_type_name() -> str:
    if graph_type == "normal":
        if directed_arcs:
            return "звичайний граф з однонапрямленими дугами"
        return "звичайний неорієнтований граф"
    if graph_type == "directed":
        return "орієнтований граф"
    return "дерево"


def total_connections() -> int:
    return len(undirected_edges) + len(directed_arcs)


def clear_animation() -> None:
    if animation_data.after_id is not None:
        try:
            root.after_cancel(animation_data.after_id)
        except tk.TclError:
            pass

    animation_data.path = None
    animation_data.search_order.clear()
    animation_data.queue_states.clear()
    animation_data.step = 0
    animation_data.opened.clear()
    animation_data.algorithm_time = 0.0
    animation_data.paused = False
    animation_data.running = False
    animation_data.after_id = None


def create_adjacency_list() -> AdjacencyList:
    adjacency_list: AdjacencyList = {
        vertex: [] for vertex in vertices
    }

    for start, end in undirected_edges:
        if start in vertices and end in vertices:
            adjacency_list[start].append(end)
            adjacency_list[end].append(start)

    for start, end in directed_arcs:
        if start in vertices and end in vertices:
            adjacency_list[start].append(end)

    return adjacency_list


def is_connected_undirected() -> bool:
    if not vertices:
        return False

    adjacency: AdjacencyList = {vertex: [] for vertex in vertices}

    for start, end in undirected_edges:
        if start in vertices and end in vertices:
            adjacency[start].append(end)
            adjacency[end].append(start)

    start_vertex = next(iter(vertices))
    queue: deque[int] = deque([start_vertex])
    visited = {start_vertex}

    while queue:
        current = queue.popleft()
        for neighbour in adjacency[current]:
            if neighbour not in visited:
                visited.add(neighbour)
                queue.append(neighbour)

    return len(visited) == len(vertices)


def has_undirected_cycle() -> bool:
    adjacency: AdjacencyList = {vertex: [] for vertex in vertices}

    for start, end in undirected_edges:
        if start in vertices and end in vertices:
            adjacency[start].append(end)
            adjacency[end].append(start)

    visited: set[int] = set()

    def dfs(current: int, parent: Optional[int]) -> bool:
        visited.add(current)

        for neighbour in adjacency[current]:
            if neighbour not in visited:
                if dfs(neighbour, current):
                    return True
            elif neighbour != parent:
                return True

        return False

    for vertex in vertices:
        if vertex not in visited and dfs(vertex, None):
            return True

    return False


def tree_state_text() -> str:
    if graph_type != "tree":
        return ""

    connected = is_connected_undirected()
    has_cycle = has_undirected_cycle()
    correct_edge_count = len(undirected_edges) == max(0, len(vertices) - 1)

    if connected and not has_cycle and correct_edge_count and not directed_arcs:
        return "Властивості дерева: зв'язне, циклів немає — структура є деревом."

    problems: list[str] = []

    if not connected:
        problems.append("структура незв'язна")
    if has_cycle:
        problems.append("виявлено цикл")
    if not correct_edge_count:
        problems.append(
            f"кількість ребер {len(undirected_edges)}, "
            f"для дерева потрібно {max(0, len(vertices) - 1)}"
        )
    if directed_arcs:
        problems.append("дерево не повинно містити дуг")

    return "Увага: після редагування це вже не дерево (" + "; ".join(problems) + ")."


def show_graph_information(message: str) -> None:
    lines = [
        message,
        f"Вид структури: {graph_type_name()}.",
        f"Кількість вершин (порядок): {len(vertices)}",
        f"Кількість зв'язків (розмір): {total_connections()}",
        f"Ребер: {len(undirected_edges)}",
        f"Дуг: {len(directed_arcs)}"
    ]

    tree_info = tree_state_text()
    if tree_info:
        lines.append(tree_info)

    status_label.config(text="\n".join(lines))


# =========================================================
# BFS
# =========================================================

def bfs(
        start_vertex: int,
        target_vertex: int,
        ascending: bool = True
) -> BFSResult:
    adjacency_list = create_adjacency_list()

    queue: deque[int] = deque([start_vertex])
    visited: set[int] = {start_vertex}
    parent: dict[int, Optional[int]] = {start_vertex: None}

    search_order: list[int] = []
    queue_states: list[list[int]] = []
    iterations = 0

    while queue:
        queue_states.append(list(queue))
        current_vertex = queue.popleft()
        search_order.append(current_vertex)
        iterations += 1

        if current_vertex == target_vertex:
            break

        neighbours = sorted(
            adjacency_list[current_vertex],
            reverse=not ascending
        )

        for neighbour in neighbours:
            if neighbour not in visited:
                visited.add(neighbour)
                parent[neighbour] = current_vertex
                queue.append(neighbour)

    if target_vertex not in visited:
        return BFSResult(
            path=None,
            search_order=search_order,
            queue_states=queue_states,
            iterations=iterations
        )

    path: list[int] = []
    current: Optional[int] = target_vertex

    while current is not None:
        path.append(current)
        current = parent[current]

    path.reverse()

    return BFSResult(
        path=path,
        search_order=search_order,
        queue_states=queue_states,
        iterations=iterations
    )


# =========================================================
# МАЛЮВАННЯ
# =========================================================

def calculate_arrow_coordinates(
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        vertex_radius: int
) -> tuple[float, float, float, float]:
    dx = x2 - x1
    dy = y2 - y1
    distance = math.hypot(dx, dy)

    if distance == 0:
        return float(x1), float(y1), float(x2), float(y2)

    unit_x = dx / distance
    unit_y = dy / distance

    return (
        x1 + unit_x * vertex_radius,
        y1 + unit_y * vertex_radius,
        x2 - unit_x * vertex_radius,
        y2 - unit_y * vertex_radius
    )


def draw_graph(
        opened: Optional[set[int]] = None,
        current: Optional[int] = None,
        path: Optional[list[int]] = None
) -> None:
    canvas.delete("all")

    opened_vertices = opened if opened is not None else set()
    path_pairs: set[tuple[int, int]] = set()

    if path is not None:
        for index in range(len(path) - 1):
            path_pairs.add((path[index], path[index + 1]))

    radius = 18

    # Неорієнтовані ребра
    for start, end in undirected_edges:
        if start not in vertices or end not in vertices:
            continue

        x1, y1 = vertices[start]
        x2, y2 = vertices[end]

        is_path = (
            (start, end) in path_pairs
            or (end, start) in path_pairs
        )

        canvas.create_line(
            x1, y1, x2, y2,
            width=4 if is_path else 2
        )

    # Орієнтовані дуги
    for start, end in directed_arcs:
        if start not in vertices or end not in vertices:
            continue

        x1, y1 = vertices[start]
        x2, y2 = vertices[end]

        ax1, ay1, ax2, ay2 = calculate_arrow_coordinates(
            x1, y1, x2, y2, radius
        )

        canvas.create_line(
            ax1, ay1, ax2, ay2,
            width=4 if (start, end) in path_pairs else 2,
            arrow=tk.LAST,
            arrowshape=(12, 15, 5)
        )

    # Вершини
    for vertex, (x, y) in vertices.items():
        if path is not None and vertex in path:
            fill_color = "lightgreen"
        elif vertex == current:
            fill_color = "gold"
        elif vertex in opened_vertices:
            fill_color = "lightblue"
        else:
            fill_color = "white"

        canvas.create_oval(
            x - radius, y - radius,
            x + radius, y + radius,
            fill=fill_color,
            outline="black",
            width=2
        )

        canvas.create_text(
            x, y,
            text=str(vertex),
            font=("Arial", 10, "bold")
        )


# =========================================================
# ВІКНО РЕЗУЛЬТАТІВ
# =========================================================

def show_results_window(
        start_vertex: int,
        target_vertex: int,
        ascending: bool
) -> None:
    result_window = tk.Toplevel(root)
    result_window.title("Результати пошуку BFS")
    result_window.geometry("720x430")
    result_window.minsize(620, 360)

    container = ttk.Frame(result_window)
    container.pack(fill="both", expand=True, padx=15, pady=15)

    ttk.Label(
        container,
        text="РЕЗУЛЬТАТИ ПОШУКУ В ШИРИНУ",
        font=("Arial", 14, "bold")
    ).pack(anchor="w", pady=(0, 10))

    path = animation_data.path
    search_order = animation_data.search_order

    if path is None:
        path_text = "Шлях не знайдено"
        path_length = "—"
    else:
        path_text = " → ".join(map(str, path))
        path_length = str(max(0, len(path) - 1))

    result_text = (
        f"Вид графа: {graph_type_name()}\n"
        f"Початкова вершина: {start_vertex}\n"
        f"Цільова вершина: {target_vertex}\n"
        f"Напрям обходу сусідів: "
        f"{'за зростанням номерів' if ascending else 'за спаданням номерів'}\n\n"
        f"Знайдений шлях: {path_text}\n"
        f"Довжина шляху (кількість переходів): {path_length}\n"
        f"Кількість ітерацій (циклів) пошуку: {len(search_order)}\n"
        f"Кількість розкритих вершин: {len(search_order)}\n"
        f"Чистий час виконання BFS: {animation_data.algorithm_time:.8f} с\n\n"
        f"Порядок розкриття вершин:\n"
        f"{', '.join(map(str, search_order))}"
    )

    text_widget = tk.Text(
        container,
        wrap="word",
        height=16,
        font=("Arial", 10)
    )
    text_widget.pack(fill="both", expand=True)
    text_widget.insert("1.0", result_text)
    text_widget.config(state="disabled")

    ttk.Button(
        container,
        text="Закрити",
        command=result_window.destroy
    ).pack(anchor="e", pady=(10, 0))


# =========================================================
# КЕРУВАННЯ АНІМАЦІЄЮ
# =========================================================

def set_search_controls_state(state: str) -> None:
    start_entry.config(state=state)
    target_entry.config(state=state)
    ascending_radio.config(state=state)
    descending_radio.config(state=state)
    normal_graph_radio.config(state=state)
    directed_graph_radio.config(state=state)
    tree_graph_radio.config(state=state)
    run_button.config(state=state)


def update_animation_buttons() -> None:
    if not animation_data.running:
        pause_button.config(state="disabled", text="Пауза")
        stop_button.config(state="disabled")
        return

    pause_button.config(
        state="normal",
        text="Продовжити" if animation_data.paused else "Пауза"
    )
    stop_button.config(state="normal")


def animate_bfs() -> None:
    if not animation_data.running or animation_data.paused:
        return

    step = animation_data.step

    if step >= len(animation_data.search_order):
        finish_animation()
        return

    current_vertex = animation_data.search_order[step]
    queue_state = animation_data.queue_states[step]

    draw_graph(
        opened=animation_data.opened,
        current=current_vertex
    )

    status_label.config(
        text=(
            f"Крок: {step + 1} із {len(animation_data.search_order)}\n"
            f"Поточна вершина: {current_vertex}\n"
            f"Черга BFS перед розкриттям: {queue_state}\n"
            f"Розкриті вершини: {sorted(animation_data.opened)}"
        )
    )

    animation_data.opened.add(current_vertex)
    animation_data.step += 1

    delay = int(float(speed_var.get()))
    animation_data.after_id = root.after(delay, animate_bfs)


def toggle_pause() -> None:
    if not animation_data.running:
        return

    animation_data.paused = not animation_data.paused

    if animation_data.paused:
        if animation_data.after_id is not None:
            try:
                root.after_cancel(animation_data.after_id)
            except tk.TclError:
                pass
            animation_data.after_id = None

        status_label.config(
            text=status_label.cget("text") + "\nПошук призупинено."
        )
    else:
        animate_bfs()

    update_animation_buttons()


def stop_animation() -> None:
    if not animation_data.running:
        return

    clear_animation()
    draw_graph()
    set_search_controls_state("normal")
    update_animation_buttons()
    status_label.config(
        text="Візуалізацію BFS зупинено користувачем."
    )


def finish_animation() -> None:
    animation_data.running = False
    animation_data.after_id = None

    path = animation_data.path
    search_order = animation_data.search_order

    if path is None:
        draw_graph(opened=animation_data.opened)
        status_label.config(
            text=(
                "Пошук завершено. Шлях не знайдено.\n"
                "Повні результати відкрито в окремому вікні."
            )
        )
    else:
        draw_graph(
            opened=animation_data.opened,
            path=path
        )

        status_label.config(
            text=(
                "Пошук завершено.\n"
                "Повні результати відкрито в окремому вікні."
            )
        )

    set_search_controls_state("normal")
    update_animation_buttons()

    try:
        start_vertex = int(start_var.get())
        target_vertex = int(target_var.get())
    except ValueError:
        return

    show_results_window(
        start_vertex,
        target_vertex,
        order_var.get() == "ascending"
    )


def run_bfs() -> None:
    try:
        start_vertex = int(start_var.get())
        target_vertex = int(target_var.get())
    except ValueError:
        messagebox.showerror(
            "Помилка",
            "Початкова та цільова вершини повинні бути цілими числами."
        )
        return

    if start_vertex not in vertices:
        messagebox.showerror(
            "Помилка",
            "Початкова вершина відсутня у графі."
        )
        return

    if target_vertex not in vertices:
        messagebox.showerror(
            "Помилка",
            "Цільова вершина відсутня у графі."
        )
        return

    ascending = order_var.get() == "ascending"

    algorithm_start = time.perf_counter()
    result = bfs(start_vertex, target_vertex, ascending)
    algorithm_end = time.perf_counter()

    clear_animation()

    animation_data.path = result.path
    animation_data.search_order = result.search_order
    animation_data.queue_states = result.queue_states
    animation_data.algorithm_time = algorithm_end - algorithm_start
    animation_data.running = True

    set_search_controls_state("disabled")
    update_animation_buttons()
    animate_bfs()


# =========================================================
# ЗМІНА ВИДУ ГРАФА
# =========================================================

def load_initial_graph(selected_type: str) -> None:
    global graph_type

    clear_animation()
    graph_type = selected_type

    vertices.clear()
    undirected_edges.clear()
    directed_arcs.clear()

    if selected_type == "tree":
        vertices.update(tree_vertices)
        undirected_edges.extend(tree_edges)

    elif selected_type == "directed":
        vertices.update(normal_vertices)
        directed_arcs.extend(directed_arcs_initial)

    else:
        vertices.update(normal_vertices)
        undirected_edges.extend(normal_edges)


def change_graph_type() -> None:
    selected_type = graph_type_var.get()
    load_initial_graph(selected_type)
    draw_graph()
    show_graph_information("Вид графа змінено.")


# =========================================================
# РЕДАГУВАННЯ ВЕРШИН
# =========================================================

def get_new_vertex_position() -> tuple[int, int]:
    canvas.update_idletasks()

    width = max(canvas.winfo_width(), 900)
    height = max(canvas.winfo_height(), 600)

    margin = 45
    min_distance = 65

    # Формуємо сітку можливих позицій на видимій області Canvas.
    candidate_positions: list[tuple[int, int]] = []

    for y in range(margin, height - margin, 70):
        for x in range(margin, width - margin, 70):
            candidate_positions.append((x, y))

    # Обираємо першу позицію, яка не накладається
    # і не розташована надто близько до наявних вершин.
    for x, y in candidate_positions:
        position_is_free = True

        for existing_x, existing_y in vertices.values():
            distance = math.hypot(x - existing_x, y - existing_y)

            if distance < min_distance:
                position_is_free = False
                break

        if position_is_free:
            return x, y

    # Запасний варіант на випадок, якщо видима область повністю заповнена.
    return margin, height - margin


def add_vertex() -> None:
    try:
        vertex = int(add_vertex_var.get())
    except ValueError:
        messagebox.showerror(
            "Помилка",
            "Номер вершини повинен бути цілим числом."
        )
        return

    if vertex <= 0:
        messagebox.showerror(
            "Помилка",
            "Номер вершини повинен бути додатним."
        )
        return

    if vertex in vertices:
        messagebox.showerror(
            "Помилка",
            f"Вершина {vertex} вже існує."
        )
        return

    vertices[vertex] = get_new_vertex_position()
    clear_animation()
    draw_graph()
    show_graph_information(f"Додано вершину {vertex}.")
    add_vertex_var.set("")


def remove_vertex() -> None:
    try:
        vertex = int(remove_vertex_var.get())
    except ValueError:
        messagebox.showerror(
            "Помилка",
            "Номер вершини повинен бути цілим числом."
        )
        return

    if vertex not in vertices:
        messagebox.showerror(
            "Помилка",
            f"Вершини {vertex} не існує."
        )
        return

    answer = messagebox.askyesno(
        "Підтвердження",
        (
            f"Видалити вершину {vertex}?\n\n"
            "Усі пов'язані з нею ребра та дуги також буде видалено."
        )
    )

    if not answer:
        return

    del vertices[vertex]

    undirected_edges[:] = [
        (start, end)
        for start, end in undirected_edges
        if start != vertex and end != vertex
    ]

    directed_arcs[:] = [
        (start, end)
        for start, end in directed_arcs
        if start != vertex and end != vertex
    ]

    clear_animation()
    draw_graph()
    show_graph_information(
        f"Вершину {vertex} та всі пов'язані з нею зв'язки видалено."
    )
    remove_vertex_var.set("")


# =========================================================
# РЕДАГУВАННЯ РЕБЕР І ДУГ
# =========================================================

def validate_connection_vertices(
        start_text: str,
        end_text: str
) -> Optional[tuple[int, int]]:
    try:
        start = int(start_text)
        end = int(end_text)
    except ValueError:
        messagebox.showerror(
            "Помилка",
            "Номери вершин повинні бути цілими числами."
        )
        return None

    if start == end:
        messagebox.showerror(
            "Помилка",
            "Не можна з'єднати вершину із самою собою."
        )
        return None

    if start not in vertices or end not in vertices:
        messagebox.showerror(
            "Помилка",
            "Одна або обидві вершини відсутні у графі."
        )
        return None

    return start, end


def undirected_edge_exists(start: int, end: int) -> bool:
    return (
        (start, end) in undirected_edges
        or (end, start) in undirected_edges
    )


def add_connection() -> None:
    result = validate_connection_vertices(
        add_edge_start_var.get(),
        add_edge_end_var.get()
    )

    if result is None:
        return

    start, end = result

    if graph_type == "directed":
        if (start, end) in directed_arcs:
            messagebox.showerror(
                "Помилка",
                f"Дуга {start} → {end} вже існує."
            )
            return

        directed_arcs.append((start, end))
        message = f"Додано дугу {start} → {end}."

    else:
        if undirected_edge_exists(start, end):
            messagebox.showerror(
                "Помилка",
                f"Ребро {start} — {end} вже існує."
            )
            return

        if (
                (start, end) in directed_arcs
                or (end, start) in directed_arcs
        ):
            messagebox.showerror(
                "Помилка",
                "Між цими вершинами вже існує однонапрямлена дуга."
            )
            return

        # Для режиму дерева не дозволяємо створювати цикл.
        if graph_type == "tree":
            undirected_edges.append((start, end))

            if has_undirected_cycle():
                undirected_edges.pop()
                messagebox.showerror(
                    "Порушення властивостей дерева",
                    (
                        "Це ребро створить цикл.\n"
                        "У дереві циклів бути не може.\n\n"
                        "Якщо потрібно збільшити дерево, спочатку "
                        "додайте нову вершину, а потім приєднайте її "
                        "одним ребром."
                    )
                )
                return
        else:
            undirected_edges.append((start, end))

        message = f"Додано ребро {start} — {end}."

    clear_animation()
    draw_graph()
    show_graph_information(message)

    add_edge_start_var.set("")
    add_edge_end_var.set("")


def remove_connection() -> None:
    result = validate_connection_vertices(
        remove_edge_start_var.get(),
        remove_edge_end_var.get()
    )

    if result is None:
        return

    start, end = result

    if graph_type == "directed":
        if (start, end) not in directed_arcs:
            messagebox.showerror(
                "Помилка",
                f"Дуги {start} → {end} не існує."
            )
            return

        directed_arcs.remove((start, end))
        message = f"Дугу {start} → {end} видалено."

    else:
        if (start, end) in undirected_edges:
            undirected_edges.remove((start, end))
        elif (end, start) in undirected_edges:
            undirected_edges.remove((end, start))
        else:
            messagebox.showerror(
                "Помилка",
                f"Ребра {start} — {end} не існує."
            )
            return

        message = f"Ребро {start} — {end} видалено."

    clear_animation()
    draw_graph()
    show_graph_information(message)

    remove_edge_start_var.set("")
    remove_edge_end_var.set("")


def convert_edge_to_arc() -> None:
    if graph_type != "normal":
        messagebox.showerror(
            "Недоступна операція",
            (
                "Заміна окремого ребра на однонапрямлену дугу "
                "виконується у режимі «Звичайний граф»."
            )
        )
        return

    result = validate_connection_vertices(
        convert_start_var.get(),
        convert_end_var.get()
    )

    if result is None:
        return

    start, end = result

    if (start, end) in undirected_edges:
        undirected_edges.remove((start, end))
    elif (end, start) in undirected_edges:
        undirected_edges.remove((end, start))
    else:
        messagebox.showerror(
            "Помилка",
            f"Ребра {start} — {end} не існує."
        )
        return

    if (start, end) not in directed_arcs:
        directed_arcs.append((start, end))

    clear_animation()
    draw_graph()
    show_graph_information(
        f"Ребро {start} — {end} замінено однонапрямленою дугою "
        f"{start} → {end}."
    )

    convert_start_var.set("")
    convert_end_var.set("")


def reverse_arc() -> None:
    result = validate_connection_vertices(
        reverse_start_var.get(),
        reverse_end_var.get()
    )

    if result is None:
        return

    start, end = result

    if (start, end) not in directed_arcs:
        messagebox.showerror(
            "Помилка",
            f"Дуги {start} → {end} не існує."
        )
        return

    directed_arcs.remove((start, end))

    if (end, start) not in directed_arcs:
        directed_arcs.append((end, start))

    clear_animation()
    draw_graph()
    show_graph_information(
        f"Напрям дуги змінено: {start} → {end} на {end} → {start}."
    )

    reverse_start_var.set("")
    reverse_end_var.set("")


def reset_graph() -> None:
    answer = messagebox.askyesno(
        "Підтвердження",
        (
            "Відновити початковий стан поточного виду графа?\n\n"
            "Усі внесені зміни буде скасовано."
        )
    )

    if not answer:
        return

    load_initial_graph(graph_type)
    draw_graph()
    show_graph_information("Початковий стан графа відновлено.")


# =========================================================
# ДОПОМІЖНИЙ GUI-БЛОК
# =========================================================

def create_connection_editor(
        parent: ttk.Frame,
        title: str,
        button_text: str,
        command: Callable[[], None]
) -> tuple[tk.StringVar, tk.StringVar]:
    frame = ttk.LabelFrame(parent, text=title)
    frame.pack(fill="x", padx=10, pady=5)

    ttk.Label(
        frame,
        text="Початкова вершина:"
    ).pack(anchor="w", padx=10, pady=(8, 3))

    start_variable = tk.StringVar()

    ttk.Entry(
        frame,
        textvariable=start_variable
    ).pack(fill="x", padx=10)

    ttk.Label(
        frame,
        text="Кінцева вершина:"
    ).pack(anchor="w", padx=10, pady=(8, 3))

    end_variable = tk.StringVar()

    ttk.Entry(
        frame,
        textvariable=end_variable
    ).pack(fill="x", padx=10)

    ttk.Button(
        frame,
        text=button_text,
        command=command
    ).pack(fill="x", padx=10, pady=8)

    return start_variable, end_variable


# =========================================================
# ВКЛАДКА "ПОШУК BFS"
# =========================================================

graph_type_frame = ttk.LabelFrame(search_tab, text="Вид графа")
graph_type_frame.pack(fill="x", padx=10, pady=(15, 5))

graph_type_var = tk.StringVar(value="normal")

normal_graph_radio = ttk.Radiobutton(
    graph_type_frame,
    text="Звичайний граф",
    variable=graph_type_var,
    value="normal",
    command=change_graph_type
)
normal_graph_radio.pack(anchor="w", padx=10, pady=(8, 3))

directed_graph_radio = ttk.Radiobutton(
    graph_type_frame,
    text="Орієнтований граф",
    variable=graph_type_var,
    value="directed",
    command=change_graph_type
)
directed_graph_radio.pack(anchor="w", padx=10, pady=3)

tree_graph_radio = ttk.Radiobutton(
    graph_type_frame,
    text="Дерево",
    variable=graph_type_var,
    value="tree",
    command=change_graph_type
)
tree_graph_radio.pack(anchor="w", padx=10, pady=(3, 8))


ttk.Label(
    search_tab,
    text="Початкова вершина:"
).pack(anchor="w", padx=15, pady=(15, 5))

start_var = tk.StringVar(value="1")
start_entry = ttk.Entry(search_tab, textvariable=start_var)
start_entry.pack(fill="x", padx=15)


ttk.Label(
    search_tab,
    text="Цільова вершина:"
).pack(anchor="w", padx=15, pady=(15, 5))

target_var = tk.StringVar(value="29")
target_entry = ttk.Entry(search_tab, textvariable=target_var)
target_entry.pack(fill="x", padx=15)


ttk.Label(
    search_tab,
    text="Порядок обходу сусідів:"
).pack(anchor="w", padx=15, pady=(20, 5))

order_var = tk.StringVar(value="ascending")

ascending_radio = ttk.Radiobutton(
    search_tab,
    text="За зростанням номерів",
    variable=order_var,
    value="ascending"
)
ascending_radio.pack(anchor="w", padx=20, pady=3)

descending_radio = ttk.Radiobutton(
    search_tab,
    text="За спаданням номерів",
    variable=order_var,
    value="descending"
)
descending_radio.pack(anchor="w", padx=20, pady=3)


ttk.Label(
    search_tab,
    text="Швидкість візуалізації:"
).pack(anchor="w", padx=15, pady=(20, 5))

speed_var = tk.DoubleVar(value=300.0)

speed_scale = ttk.Scale(
    search_tab,
    from_=1000,
    to=100,
    variable=speed_var,
    orient="horizontal"
)
speed_scale.pack(fill="x", padx=15)

ttk.Label(
    search_tab,
    text="повільніше                    швидше",
    font=("Arial", 8)
).pack(fill="x", padx=15)


run_button = ttk.Button(
    search_tab,
    text="Запустити BFS",
    command=run_bfs
)
run_button.pack(fill="x", padx=15, pady=(20, 5))

animation_buttons_frame = ttk.Frame(search_tab)
animation_buttons_frame.pack(fill="x", padx=15, pady=(0, 10))
animation_buttons_frame.columnconfigure(0, weight=1)
animation_buttons_frame.columnconfigure(1, weight=1)

pause_button = ttk.Button(
    animation_buttons_frame,
    text="Пауза",
    command=toggle_pause,
    state="disabled"
)
pause_button.grid(row=0, column=0, sticky="ew", padx=(0, 3))

stop_button = ttk.Button(
    animation_buttons_frame,
    text="Зупинити",
    command=stop_animation,
    state="disabled"
)
stop_button.grid(row=0, column=1, sticky="ew", padx=(3, 0))


# =========================================================
# ЛЕГЕНДА
# =========================================================

legend_frame = ttk.LabelFrame(search_tab, text="Легенда візуалізації")
legend_frame.pack(fill="x", padx=10, pady=(5, 15))

legend_canvas = tk.Canvas(
    legend_frame,
    height=105,
    highlightthickness=0
)
legend_canvas.pack(fill="x", padx=8, pady=5)

legend_items = [
    ("white", "Невідвідана вершина"),
    ("lightblue", "Розкрита вершина"),
    ("gold", "Поточна вершина"),
    ("lightgreen", "Вершина знайденого шляху")
]

for index, (fill_color, label) in enumerate(legend_items):
    y = 15 + index * 23
    legend_canvas.create_oval(
        5, y - 7, 19, y + 7,
        fill=fill_color,
        outline="black"
    )
    legend_canvas.create_text(
        28, y,
        text=label,
        anchor="w",
        font=("Arial", 9)
    )


# =========================================================
# ВКЛАДКА "РЕДАГУВАННЯ ГРАФА"
# =========================================================

add_vertex_frame = ttk.LabelFrame(edit_tab, text="Додати вершину")
add_vertex_frame.pack(fill="x", padx=10, pady=(15, 5))

ttk.Label(
    add_vertex_frame,
    text="Номер нової вершини:"
).pack(anchor="w", padx=10, pady=(8, 3))

add_vertex_var = tk.StringVar()

ttk.Entry(
    add_vertex_frame,
    textvariable=add_vertex_var
).pack(fill="x", padx=10)

ttk.Button(
    add_vertex_frame,
    text="Додати вершину",
    command=add_vertex
).pack(fill="x", padx=10, pady=8)


remove_vertex_frame = ttk.LabelFrame(edit_tab, text="Видалити вершину")
remove_vertex_frame.pack(fill="x", padx=10, pady=5)

ttk.Label(
    remove_vertex_frame,
    text="Номер вершини:"
).pack(anchor="w", padx=10, pady=(8, 3))

remove_vertex_var = tk.StringVar()

ttk.Entry(
    remove_vertex_frame,
    textvariable=remove_vertex_var
).pack(fill="x", padx=10)

ttk.Button(
    remove_vertex_frame,
    text="Видалити вершину",
    command=remove_vertex
).pack(fill="x", padx=10, pady=8)


add_edge_start_var, add_edge_end_var = create_connection_editor(
    edit_tab,
    "Додати ребро / дугу",
    "Додати ребро / дугу",
    add_connection
)

remove_edge_start_var, remove_edge_end_var = create_connection_editor(
    edit_tab,
    "Видалити ребро / дугу",
    "Видалити ребро / дугу",
    remove_connection
)

convert_start_var, convert_end_var = create_connection_editor(
    edit_tab,
    "Замінити ребро на однонапрямлену дугу",
    "Замінити ребро на дугу",
    convert_edge_to_arc
)

reverse_start_var, reverse_end_var = create_connection_editor(
    edit_tab,
    "Змінити напрям дуги",
    "Розвернути дугу",
    reverse_arc
)

ttk.Separator(
    edit_tab,
    orient="horizontal"
).pack(fill="x", padx=10, pady=(15, 10))

ttk.Button(
    edit_tab,
    text="Відновити початковий граф",
    command=reset_graph
).pack(fill="x", padx=10, pady=(0, 15))


# =========================================================
# ПОЧАТКОВИЙ СТАН
# =========================================================

draw_graph()
show_graph_information("Програма готова до роботи.")
update_animation_buttons()

root.mainloop()

