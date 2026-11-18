import tkinter as tk
from tkinter import ttk
import time


class RasterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Лабораторная работа №3 — Базовые растровые алгоритмы")
        self.root.geometry("1000x650")

        # Панель управления (Верхняя)
        control_frame = ttk.Frame(root, padding=10)
        control_frame.pack(side=tk.TOP, fill=tk.X)

        # Выбор алгоритма
        ttk.Label(control_frame, text="Алгоритм:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.algo_var = tk.StringVar(value="Брезенхем (отрезок)")
        algos = [
            "Пошаговый",
            "ЦДА",
            "Брезенхем (отрезок)",
            "Брезенхем (окружность)",
            "Кастл-Питвей (доп.)",
            "Алгоритм Ву (сглаживание, доп.)"
        ]
        self.algo_combo = ttk.Combobox(control_frame, textvariable=self.algo_var, values=algos, state="readonly", width=28)
        self.algo_combo.grid(row=0, column=1, padx=5, pady=5)
        self.algo_combo.bind("<<ComboboxSelected>>", self.on_algo_change)

        # Координаты X1, Y1 / X2, Y2 (или R)
        self.lbl_x1 = ttk.Label(control_frame, text="X1:")
        self.lbl_x1.grid(row=0, column=2, padx=(15, 2))
        self.entry_x1 = ttk.Entry(control_frame, width=6)
        self.entry_x1.insert(0, "-8")
        self.entry_x1.grid(row=0, column=3, padx=2)

        self.lbl_y1 = ttk.Label(control_frame, text="Y1:")
        self.lbl_y1.grid(row=0, column=4, padx=(10, 2))
        self.entry_y1 = ttk.Entry(control_frame, width=6)
        self.entry_y1.insert(0, "-5")
        self.entry_y1.grid(row=0, column=5, padx=2)

        self.lbl_x2 = ttk.Label(control_frame, text="X2 / R:")
        self.lbl_x2.grid(row=0, column=6, padx=(10, 2))
        self.entry_x2 = ttk.Entry(control_frame, width=6)
        self.entry_x2.insert(0, "12")
        self.entry_x2.grid(row=0, column=7, padx=2)

        self.lbl_y2 = ttk.Label(control_frame, text="Y2:")
        self.lbl_y2.grid(row=0, column=8, padx=(10, 2))
        self.entry_y2 = ttk.Entry(control_frame, width=6)
        self.entry_y2.insert(0, "9")
        self.entry_y2.grid(row=0, column=9, padx=2)

        # Масштаб (размер клетки)
        ttk.Label(control_frame, text="Клетка (px):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.scale_var = tk.IntVar(value=25)
        self.scale_slider = ttk.Scale(control_frame, from_=10, to=50, variable=self.scale_var, command=lambda e: self.draw())
        self.scale_slider.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        # Кнопка Отрисовать
        btn_draw = ttk.Button(control_frame, text="Отрисовать", command=self.draw)
        btn_draw.grid(row=0, column=10, padx=15, pady=5)

        # Поле вывода времени и пикселей
        self.info_label = ttk.Label(control_frame, text="Время работы: - | Пикселей: -", font=("Arial", 10, "bold"))
        self.info_label.grid(row=1, column=2, columnspan=9, padx=10, pady=5, sticky=tk.W)

        # Холст отрисовки
        self.canvas = tk.Canvas(root, bg="white")
        self.canvas.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        self.canvas.bind("<Configure>", lambda e: self.draw())

    def on_algo_change(self, event=None):
        if self.algo_var.get() == "Брезенхем (окружность)":
            self.lbl_x1.config(text="Xc:")
            self.lbl_y1.config(text="Yc:")
            self.lbl_x2.config(text="R:")
            self.lbl_y2.grid_remove()
            self.entry_y2.grid_remove()
        else:
            self.lbl_x1.config(text="X1:")
            self.lbl_y1.config(text="Y1:")
            self.lbl_x2.config(text="X2:")
            self.lbl_y2.grid()
            self.entry_y2.grid()
        self.draw()

    # Безопасный считыватель чисел: возвращает None, если поле пустое или не число
    def safe_get(self, entry):
        text = entry.get().strip()
        if not text:
            return None
        try:
            return int(text)
        except ValueError:
            return None

    # 1. Пошаговый алгоритм
    def step_by_step(self, x1, y1, x2, y2):
        pixels = []
        dx = x2 - x1
        dy = y2 - y1
        if abs(dx) >= abs(dy):
            if dx == 0:
                return [(x1, y1)]
            k = dy / dx
            b = y1 - k * x1
            step = 1 if x2 >= x1 else -1
            for x in range(x1, x2 + step, step):
                pixels.append((x, round(k * x + b)))
        else:
            k = dx / dy
            b = x1 - k * y1
            step = 1 if y2 >= y1 else -1
            for y in range(y1, y2 + step, step):
                pixels.append((round(k * y + b), y))
        return pixels

    # 2. Алгоритм ЦДА
    def dda(self, x1, y1, x2, y2):
        pixels = []
        dx = x2 - x1
        dy = y2 - y1
        steps = max(abs(dx), abs(dy))
        if steps == 0:
            return [(x1, y1)]
        x_inc = dx / steps
        y_inc = dy / steps
        x, y = float(x1), float(y1)
        for _ in range(steps + 1):
            pixels.append((round(x), round(y)))
            x += x_inc
            y += y_inc
        return pixels

    # 3. Алгоритм Брезенхема (отрезок)
    def bresenham_line(self, x1, y1, x2, y2):
        pixels = []
        x, y = x1, y1
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x2 >= x1 else -1
        sy = 1 if y2 >= y1 else -1

        if dy <= dx:
            err = 2 * dy - dx
            for _ in range(dx + 1):
                pixels.append((x, y))
                if err >= 0:
                    y += sy
                    err -= 2 * dx
                x += sx
                err += 2 * dy
        else:
            err = 2 * dx - dy
            for _ in range(dy + 1):
                pixels.append((x, y))
                if err >= 0:
                    x += sx
                    err -= 2 * dy
                y += sy
                err += 2 * dx
        return pixels

    # 4. Алгоритм Брезенхема (окружность)
    def bresenham_circle(self, xc, yc, r):
        r = abs(r)
        pixels = set()
        x = 0
        y = r
        d = 3 - 2 * r

        def add_sym(cx, cy, px, py):
            pixels.update([
                (cx + px, cy + py), (cx - px, cy + py),
                (cx + px, cy - py), (cx - px, cy - py),
                (cx + py, cy + px), (cx - py, cy + px),
                (cx + py, cy - px), (cx - py, cy - px)
            ])

        add_sym(xc, yc, x, y)
        while y >= x:
            x += 1
            if d > 0:
                y -= 1
                d = d + 4 * (x - y) + 10
            else:
                d = d + 4 * x + 6
            add_sym(xc, yc, x, y)
        return list(pixels)

    # 5. Алгоритм Кастла-Питвея (доп.)
    def castle_piteway(self, x1, y1, x2, y2):
        dx = x2 - x1
        dy = y2 - y1
        sx = 1 if dx >= 0 else -1
        sy = 1 if dy >= 0 else -1
        dx, dy = abs(dx), abs(dy)

        steep = dy > dx
        if steep:
            dx, dy = dy, dx

        if dx == 0:
            return [(x1, y1)]

        n_D = dy
        n_S = dx - dy

        def build_seq(S_pat, D_pat, c_S, c_D):
            if c_D == 0:
                return S_pat * c_S
            if c_S == 0:
                return D_pat * c_D
            if c_S >= c_D:
                q = c_S // c_D
                rem = c_S % c_D
                new_S = S_pat * q + D_pat
                return build_seq(new_S, S_pat, c_D, rem)
            else:
                q = c_D // c_S
                rem = c_D % c_S
                new_D = D_pat * q + S_pat
                return build_seq(D_pat, new_D, rem, c_S)

        seq = build_seq(['S'], ['D'], n_S, n_D)
        curr_x, curr_y = x1, y1
        pixels = [(curr_x, curr_y)]
        for step in seq:
            if step == 'S':
                if steep:
                    curr_y += sy
                else:
                    curr_x += sx
            else:
                curr_x += sx
                curr_y += sy
            pixels.append((curr_x, curr_y))
        return pixels

    # 6. Алгоритм Ву сглаживания (доп.)
    def wu_line(self, x1, y1, x2, y2):
        pixels = []

        def ipart(x): return int(x)
        def fpart(x): return x - int(x)
        def rfpart(x): return 1 - fpart(x)

        steep = abs(y2 - y1) > abs(x2 - x1)
        if steep:
            x1, y1 = y1, x1
            x2, y2 = y2, x2
        if x1 > x2:
            x1, x2 = x2, x1
            y1, y2 = y2, y1

        dx = x2 - x1
        dy = y2 - y1
        gradient = dy / dx if dx != 0 else 1.0

        xend = round(x1)
        yend = y1 + gradient * (xend - x1)
        xgap = rfpart(x1 + 0.5)
        xpxl1 = xend
        ypxl1 = ipart(yend)

        if steep:
            pixels.append((ypxl1, xpxl1, rfpart(yend) * xgap))
            pixels.append((ypxl1 + 1, xpxl1, fpart(yend) * xgap))
        else:
            pixels.append((xpxl1, ypxl1, rfpart(yend) * xgap))
            pixels.append((xpxl1, ypxl1 + 1, fpart(yend) * xgap))

        intery = yend + gradient
        xend = round(x2)
        yend = y2 + gradient * (xend - x2)
        xpxl2 = xend
        ypxl2 = ipart(yend)

        for x in range(xpxl1 + 1, xpxl2):
            if steep:
                pixels.append((ipart(intery), x, rfpart(intery)))
                pixels.append((ipart(intery) + 1, x, fpart(intery)))
            else:
                pixels.append((x, ipart(intery), rfpart(intery)))
                pixels.append((x, ipart(intery) + 1, fpart(intery)))
            intery += gradient

        if steep:
            pixels.append((ypxl2, xpxl2, rfpart(yend) * xgap))
            pixels.append((ypxl2 + 1, xpxl2, fpart(yend) * xgap))
        else:
            pixels.append((xpxl2, ypxl2, rfpart(yend) * xgap))
            pixels.append((xpxl2, ypxl2 + 1, fpart(yend) * xgap))

        return pixels

    # Отрисовка координатной сетки и пикселей
    def draw(self):
        self.canvas.delete("all")
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw <= 1 or ch <= 1:
            return

        cell = self.scale_var.get()
        ox = cw // 2
        oy = ch // 2

        # 1. Отрисовка фоновой сетки
        for x in range(ox % cell, cw, cell):
            self.canvas.create_line(x, 0, x, ch, fill="#e5e5e5")
        for y in range(oy % cell, ch, cell):
            self.canvas.create_line(0, y, cw, y, fill="#e5e5e5")

        # 2. Главные оси X и Y
        self.canvas.create_line(0, oy, cw, oy, fill="black", width=2)
        self.canvas.create_line(ox, 0, ox, ch, fill="black", width=2)

        # Подписи координат
        for x_grid in range(-cw // (2 * cell), cw // (2 * cell) + 1):
            if x_grid != 0:
                px = ox + x_grid * cell
                self.canvas.create_line(px, oy - 3, px, oy + 3, fill="black")
                self.canvas.create_text(px, oy + 12, text=str(x_grid), font=("Arial", 8))

        for y_grid in range(-ch // (2 * cell), ch // (2 * cell) + 1):
            if y_grid != 0:
                py = oy - y_grid * cell
                self.canvas.create_line(ox - 3, py, ox + 3, py, fill="black")
                self.canvas.create_text(ox - 12, py, text=str(y_grid), font=("Arial", 8))

        self.canvas.create_text(ox - 10, oy + 12, text="0", font=("Arial", 8, "bold"))

        # 3. Считывание значений и проверка на полноту ввода
        algo = self.algo_var.get()
        val1 = self.safe_get(self.entry_x1)
        val2 = self.safe_get(self.entry_y1)
        val3 = self.safe_get(self.entry_x2)
        val4 = self.safe_get(self.entry_y2) if algo != "Брезенхем (окружность)" else 0

        # Если хотя бы одно поле незаполнено, очищаем рисунок и выходим
        if val1 is None or val2 is None or val3 is None or val4 is None:
            self.info_label.config(text="Время работы: - | Закрашено пикселей: -")
            return

        iterations = 1000
        t0 = time.perf_counter()

        if algo == "Пошаговый":
            for _ in range(iterations):
                pixels = self.step_by_step(val1, val2, val3, val4)
        elif algo == "ЦДА":
            for _ in range(iterations):
                pixels = self.dda(val1, val2, val3, val4)
        elif algo == "Брезенхем (отрезок)":
            for _ in range(iterations):
                pixels = self.bresenham_line(val1, val2, val3, val4)
        elif algo == "Брезенхем (окружность)":
            for _ in range(iterations):
                pixels = self.bresenham_circle(val1, val2, val3)
        elif algo == "Кастл-Питвей (доп.)":
            for _ in range(iterations):
                pixels = self.castle_piteway(val1, val2, val3, val4)
        elif algo == "Алгоритм Ву (сглаживание, доп.)":
            for _ in range(iterations):
                pixels = self.wu_line(val1, val2, val3, val4)

        t1 = time.perf_counter()
        avg_us = ((t1 - t0) / iterations) * 1e6
        self.info_label.config(text=f"Время работы: {avg_us:.2f} мкс | Закрашено пикселей: {len(pixels)}")

        # 4. Закрашивание пикселей
        for item in pixels:
            if len(item) == 3:  # Алгоритм Ву (x, y, intensity)
                gx, gy, intensity = item
                alpha = int(255 * (1 - max(0.0, min(1.0, intensity))))
                color = f"#{alpha:02x}{alpha:02x}{alpha:02x}"
            else:
                gx, gy = item
                color = "#4A90E2"

            x_left = ox + gx * cell - cell // 2
            y_top = oy - gy * cell - cell // 2
            x_right = x_left + cell
            y_bottom = y_top + cell
            self.canvas.create_rectangle(x_left, y_top, x_right, y_bottom, fill=color, outline="#707070")

        # 5. Идеальная линия или окружность поверх пикселей
        if algo == "Брезенхем (окружность)":
            cx_px = ox + val1 * cell
            cy_px = oy - val2 * cell
            r_px = abs(val3) * cell
            self.canvas.create_oval(cx_px - r_px, cy_px - r_px, cx_px + r_px, cy_px + r_px, outline="#E74C3C", width=2)
        else:
            x1_px = ox + val1 * cell
            y1_px = oy - val2 * cell
            x2_px = ox + val3 * cell
            y2_px = oy - val4 * cell
            self.canvas.create_line(x1_px, y1_px, x2_px, y2_px, fill="#E74C3C", width=2)


if __name__ == "__main__":
    root = tk.Tk()
    app = RasterApp(root)
    root.mainloop()