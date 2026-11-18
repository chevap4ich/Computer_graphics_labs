import tkinter as tk
from tkinter import filedialog
import math

# погрешность поиска границы окна и допуск при проверке попадания в окно
EPS = 1e-6
TOL = 1e-5


# алгоритмы

def code(x, y, win):
    # код точки относительно окна: 4 бита (лево, право, низ, верх)
    xmin, ymin, xmax, ymax = win
    c = 0
    if x < xmin - TOL:
        c |= 1
    if x > xmax + TOL:
        c |= 2
    if y < ymin - TOL:
        c |= 4
    if y > ymax + TOL:
        c |= 8
    return c


def nearest_visible(a, b, win):
    # ищем делением пополам ближайшую к точке a видимую точку отрезка ab
    # в конце точки a и b почти совпадают, возвращаем b (она на видимой стороне)
    while math.dist(a, b) > EPS:
        m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        if code(a[0], a[1], win) & code(m[0], m[1], win):
            a = m  # часть a-m целиком невидима, отбрасываем её
        else:
            b = m
    return b


def midpoint_clip(p1, p2, win):
    # отсечение отрезка алгоритмом средней точки, возвращает видимую часть или None
    c1 = code(p1[0], p1[1], win)
    c2 = code(p2[0], p2[1], win)
    if c1 == 0 and c2 == 0:
        return p1, p2  # отрезок целиком внутри
    if c1 & c2:
        return None  # отрезок целиком снаружи
    a = nearest_visible(p1, p2, win)
    b = nearest_visible(p2, p1, win)
    # если найденные точки вне окна, отрезок окно не пересекает
    if code(a[0], a[1], win) or code(b[0], b[1], win):
        return None
    if math.dist(a, b) < 2 * TOL:
        return None
    return a, b


def cut_polygon(points, inside, cross):
    # отсечение многоугольника одной границей окна
    result = []
    for i in range(len(points)):
        cur = points[i]
        prev = points[i - 1]
        if inside(cur):
            if not inside(prev):
                result.append(cross(prev, cur))
            result.append(cur)
        elif inside(prev):
            result.append(cross(prev, cur))
    return result


def clip_polygon(poly, win):
    # алгоритм Сазерленда-Коэна: по очереди отсекаем четырьмя границами окна
    xmin, ymin, xmax, ymax = win

    def cross_x(c):
        # пересечение отрезка с вертикальной прямой x = c
        def f(p, q):
            t = (c - p[0]) / (q[0] - p[0])
            return (c, p[1] + t * (q[1] - p[1]))
        return f

    def cross_y(c):
        # пересечение отрезка с горизонтальной прямой y = c
        def f(p, q):
            t = (c - p[1]) / (q[1] - p[1])
            return (p[0] + t * (q[0] - p[0]), c)
        return f

    borders = [
        (lambda p: p[0] >= xmin, cross_x(xmin)),
        (lambda p: p[0] <= xmax, cross_x(xmax)),
        (lambda p: p[1] >= ymin, cross_y(ymin)),
        (lambda p: p[1] <= ymax, cross_y(ymax)),
    ]
    for inside, cross in borders:
        if not poly:
            break
        poly = cut_polygon(poly, inside, cross)
    return poly


def is_convex(poly):
    # многоугольник выпуклый, если все векторные произведения соседних рёбер одного знака
    sign = 0
    n = len(poly)
    for i in range(n):
        a, b, c = poly[i], poly[(i + 1) % n], poly[(i + 2) % n]
        cr = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
        if cr != 0:
            if sign == 0:
                sign = 1 if cr > 0 else -1
            elif (cr > 0) != (sign > 0):
                return False
    return True


# ---------- чтение файлов ----------

def read_numbers(path):
    with open(path, encoding="utf-8") as f:
        return [float(t) for t in f.read().replace("*", " ").split() if _is_number(t)]


def _is_number(t):
    try:
        float(t)
        return True
    except ValueError:
        return False


def read_segments(path):
    # формат: n, затем n строк x1 y1 x2 y2, затем xmin ymin xmax ymax
    nums = read_numbers(path)
    n = int(nums[0])
    segs = []
    for i in range(n):
        x1, y1, x2, y2 = nums[1 + 4 * i: 5 + 4 * i]
        segs.append(((x1, y1), (x2, y2)))
    return segs, make_window(nums[1 + 4 * n: 5 + 4 * n])


def read_polygon(path):
    # формат: n, затем n строк x y, затем xmin ymin xmax ymax
    nums = read_numbers(path)
    n = int(nums[0])
    poly = [(nums[1 + 2 * i], nums[2 + 2 * i]) for i in range(n)]
    return poly, make_window(nums[1 + 2 * n: 5 + 2 * n])


def make_window(v):
    if len(v) != 4:
        raise ValueError("не хватает координат окна")
    xmin, ymin, xmax, ymax = v
    return (min(xmin, xmax), min(ymin, ymax), max(xmin, xmax), max(ymin, ymax))


# ---------- приложение ----------

class App:
    PAD = 40

    def __init__(self, root):
        self.root = root
        root.title("Лабораторная работа №4 (Вариант 3)")

        self.mode = None      # "segments" или "polygon"
        self.segments = []
        self.polygon = []
        self.window = None
        self.result = None    # результат отсечения

        panel = tk.Frame(root, padx=10, pady=5)
        panel.pack(side=tk.TOP, fill=tk.X)
        tk.Button(panel, text="Открыть файл с отрезками", command=self.load_segments).pack(side=tk.LEFT, padx=4)
        tk.Button(panel, text="Открыть файл с многоугольником", command=self.load_polygon).pack(side=tk.LEFT, padx=4)
        tk.Button(panel, text="Выполнить отсечение", command=self.do_clip, bg="#d0f0d0").pack(side=tk.LEFT, padx=4)

        self.info = tk.Label(root, text="Откройте файл с данными", font=("Arial", 11, "bold"))
        self.info.pack(side=tk.TOP, pady=3)

        # размер поля рисования подбираем под экран
        self.w = int(min(800, root.winfo_screenwidth() * 0.8))
        self.h = int(min(560, root.winfo_screenheight() * 0.6))
        self.canvas = tk.Canvas(root, width=self.w, height=self.h, bg="white")
        self.canvas.pack(padx=10, pady=5)

    def load_segments(self):
        path = filedialog.askopenfilename(filetypes=[("Текстовые файлы", "*.txt")])
        if not path:
            return
        try:
            self.segments, self.window = read_segments(path)
        except (ValueError, IndexError):
            self.info.config(text="Ошибка: неверный формат файла")
            return
        self.mode = "segments"
        self.result = None
        self.info.config(text=f"Загружено отрезков: {len(self.segments)}")
        self.redraw()

    def load_polygon(self):
        path = filedialog.askopenfilename(filetypes=[("Текстовые файлы", "*.txt")])
        if not path:
            return
        try:
            self.polygon, self.window = read_polygon(path)
        except (ValueError, IndexError):
            self.info.config(text="Ошибка: неверный формат файла")
            return
        self.mode = "polygon"
        self.result = None
        if is_convex(self.polygon):
            self.info.config(text=f"Загружен многоугольник: {len(self.polygon)} вершин")
        else:
            self.info.config(text="Внимание: многоугольник невыпуклый, результат может быть неверным")
        self.redraw()

    def do_clip(self):
        if self.mode is None:
            self.info.config(text="Сначала откройте файл")
            return
        if self.mode == "segments":
            self.result = []
            for p1, p2 in self.segments:
                part = midpoint_clip(p1, p2, self.window)
                if part:
                    self.result.append(part)
            self.info.config(text=f"Алгоритм средней точки: видимых отрезков {len(self.result)} из {len(self.segments)}")
        else:
            self.result = clip_polygon(self.polygon, self.window)
            self.info.config(text=f"Алгоритм отсечения выпуклого многоугольника: вершин после отсечения {len(self.result)}")
        self.redraw()

    # ----- рисование -----

    def all_points(self):
        pts = [(0, 0), (self.window[0], self.window[1]), (self.window[2], self.window[3])]
        for p1, p2 in self.segments if self.mode == "segments" else []:
            pts += [p1, p2]
        if self.mode == "polygon":
            pts += self.polygon
        return pts

    def set_scale(self):
        # границы сцены и общий масштаб по обеим осям
        pts = self.all_points()
        self.x0 = min(p[0] for p in pts)
        self.x1 = max(p[0] for p in pts)
        self.y0 = min(p[1] for p in pts)
        self.y1 = max(p[1] for p in pts)
        rx = max(self.x1 - self.x0, 1e-9)
        ry = max(self.y1 - self.y0, 1e-9)
        self.scale = min((self.w - 2 * self.PAD) / rx, (self.h - 2 * self.PAD) / ry)

    def sx(self, x):
        return self.PAD + (x - self.x0) * self.scale

    def sy(self, y):
        return self.h - self.PAD - (y - self.y0) * self.scale

    def nice_step(self):
        # шаг сетки 1, 2 или 5 умножить на степень десяти
        raw = max(self.x1 - self.x0, self.y1 - self.y0) / 10
        power = 10 ** math.floor(math.log10(raw))
        for k in (1, 2, 5, 10):
            if raw <= k * power:
                return k * power

    def draw_axes(self):
        c = self.canvas
        step = self.nice_step()
        # сетка и подписи по x
        x = math.ceil(self.x0 / step) * step
        while x <= self.x1 + 1e-9:
            c.create_line(self.sx(x), self.sy(self.y0), self.sx(x), self.sy(self.y1), fill="#e8e8e8")
            c.create_text(self.sx(x), self.sy(0) + 10, text=f"{x:g}", font=("Arial", 8))
            x += step
        # сетка и подписи по y
        y = math.ceil(self.y0 / step) * step
        while y <= self.y1 + 1e-9:
            c.create_line(self.sx(self.x0), self.sy(y), self.sx(self.x1), self.sy(y), fill="#e8e8e8")
            c.create_text(self.sx(0) - 14, self.sy(y), text=f"{y:g}", font=("Arial", 8))
            y += step
        # оси координат
        c.create_line(self.sx(self.x0), self.sy(0), self.sx(self.x1), self.sy(0), fill="black", arrow=tk.LAST)
        c.create_line(self.sx(0), self.sy(self.y0), self.sx(0), self.sy(self.y1), fill="black", arrow=tk.LAST)
        c.create_text(self.sx(self.x1), self.sy(0) - 12, text="x")
        c.create_text(self.sx(0) + 12, self.sy(self.y1), text="y")

    def redraw(self):
        c = self.canvas
        c.delete("all")
        if self.window is None:
            return
        self.set_scale()
        self.draw_axes()

        # отсекающее окно (синий)
        xmin, ymin, xmax, ymax = self.window
        c.create_rectangle(self.sx(xmin), self.sy(ymax), self.sx(xmax), self.sy(ymin), outline="blue", width=2)

        # исходные данные (красный)
        if self.mode == "segments":
            for p1, p2 in self.segments:
                c.create_line(self.sx(p1[0]), self.sy(p1[1]), self.sx(p2[0]), self.sy(p2[1]), fill="red", dash=(4, 3))
        else:
            flat = [v for p in self.polygon for v in (self.sx(p[0]), self.sy(p[1]))]
            c.create_polygon(flat, outline="red", fill="", dash=(4, 3))

        # видимые части (зелёный)
        if self.result and (self.mode == "segments" or len(self.result) >= 3):
            if self.mode == "segments":
                for p1, p2 in self.result:
                    c.create_line(self.sx(p1[0]), self.sy(p1[1]), self.sx(p2[0]), self.sy(p2[1]), fill="green", width=3)
            else:
                flat = [v for p in self.result for v in (self.sx(p[0]), self.sy(p[1]))]
                c.create_polygon(flat, outline="green", fill="#b8e8b8", width=3)

        # легенда
        c.create_text(10, 10, anchor="nw", text="синий - окно, красный - исходные данные, зелёный - видимая часть")


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
