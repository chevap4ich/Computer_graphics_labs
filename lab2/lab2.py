import tkinter as tk
from tkinter import filedialog, ttk
import tkinter.font as tkfont
from PIL import Image, ImageTk, ImageDraw
import numpy as np


# ---------- Маски (ядра) из лекции 4 ----------
# Сумма весов W != 0 -> результат делится на W (формула дискретной свёртки
# из лекции: f'(m,n) = 1/W * sum f(m+i,n+j) * w(i,j)).
# Для масок с W = 0 (лапласиан, LoG) деления нет: это "отклик" фильтра.
KERNEL_LAPLACE = np.array([[0, -1, 0],
                           [-1, 4, -1],
                           [0, -1, 0]], dtype=np.float32)

KERNEL_SHARP_5 = np.array([[0, -1, 0],
                           [-1, 5, -1],
                           [0, -1, 0]], dtype=np.float32)

KERNEL_SHARP_9 = np.array([[-1, -1, -1],
                           [-1, 9, -1],
                           [-1, -1, -1]], dtype=np.float32)

KERNEL_SHARP_121 = np.array([[1, -2, 1],
                             [-2, 5, -2],
                             [1, -2, 1]], dtype=np.float32)

KERNEL_SHARP_20 = np.array([[0, -1, 0],
                            [-1, 20, -1],
                            [0, -1, 0]], dtype=np.float32)  # W = 16 -> мягкий эффект

KERNEL_LOG = np.array([[0, 0, -1, 0, 0],
                       [0, -1, -2, -1, 0],
                       [-1, -2, 16, -2, -1],
                       [0, -1, -2, -1, 0],
                       [0, 0, -1, 0, 0]], dtype=np.float32)


def convolve(arr, kernel):
    """Дискретная свёртка с маской; границы дополняются копией крайних пикселей.
    Если сумма весов W != 0, результат нормируется делением на W."""
    a = arr.astype(np.float32)
    kernel = np.asarray(kernel, dtype=np.float32)
    kh, kw = kernel.shape
    ph, pw = kh // 2, kw // 2
    h, w = a.shape
    padded = np.pad(a, ((ph, ph), (pw, pw)), mode="edge")
    out = np.zeros((h, w), dtype=np.float32)
    for i in range(kh):
        for j in range(kw):
            if kernel[i, j] != 0:
                out += kernel[i, j] * padded[i:i + h, j:j + w]
    weight = kernel.sum()
    if weight != 0:
        out /= weight
    return out


def gaussian_blur(arr, sigma):
    """Гауссово размытие через два одномерных прохода (разделимое ядро)."""
    a = arr.astype(np.float32)
    r = max(1, int(np.ceil(3 * sigma)))
    x = np.arange(-r, r + 1, dtype=np.float32)
    g = np.exp(-(x ** 2) / (2.0 * sigma ** 2))
    g /= g.sum()
    h, w = a.shape
    padded = np.pad(a, ((r, r), (r, r)), mode="edge")
    tmp = np.zeros((h, w + 2 * r), dtype=np.float32)
    for i, gi in enumerate(g):                     # проход по строкам (вертикально)
        tmp += gi * padded[i:i + h, :]
    out = np.zeros((h, w), dtype=np.float32)
    for j, gj in enumerate(g):                     # проход по столбцам (горизонтально)
        out += gj * tmp[:, j:j + w]
    return out


def to_uint8(arr):
    return np.clip(np.round(arr), 0, 255).astype(np.uint8)


def sharpen_mask(gray, kernel):
    """Повышение резкости маской из лекции (W != 0)."""
    return to_uint8(convolve(gray, kernel))


def sharpen_laplace_k(gray, k):
    """g = f + k * L(f), где L - лапласиан (4 соседа). При k = 1 равно маске с центром 5."""
    f = gray.astype(np.float32)
    return to_uint8(f + k * convolve(gray, KERNEL_LAPLACE))


def laplace_response(gray, kernel):
    """Отклик лапласиана / LoG для показа: сдвиг на 128, чтобы были видны
    и положительные, и отрицательные значения."""
    return to_uint8(convolve(gray, kernel) + 128.0)


def gradient_magnitude(gray):
    """Градиент по лекции: Gx = f(x+1,y)-f(x,y), Gy = f(x,y+1)-f(x,y), |grad| ~ |Gx|+|Gy|."""
    f = gray.astype(np.float32)
    gx = np.zeros_like(f)
    gy = np.zeros_like(f)
    gx[:, :-1] = f[:, 1:] - f[:, :-1]
    gy[:-1, :] = f[1:, :] - f[:-1, :]
    return to_uint8(np.abs(gx) + np.abs(gy))


def unsharp_mask(gray, k, sigma):
    """sharp = original + k * (original - blurred)."""
    f = gray.astype(np.float32)
    blurred = gaussian_blur(gray, sigma)
    return to_uint8(f + k * (f - blurred))


# ---------- Гистограмма, контрастирование, эквализация ----------
def histogram(arr):
    """h(i) = число пикселей с яркостью i, i = 0..255."""
    return np.bincount(arr.ravel(), minlength=256).astype(np.int64)


def linear_contrast(gray, clip_percent=0.0):
    """f' = 255 / (f_max - f_min) * (f - f_min).
    clip_percent > 0 -> f_min/f_max берутся как перцентили (устойчивость к шуму)."""
    f = gray.astype(np.float32)
    if clip_percent > 0:
        f_min, f_max = np.percentile(f, [clip_percent, 100.0 - clip_percent])
    else:
        f_min, f_max = float(f.min()), float(f.max())
    if f_max <= f_min:
        return gray.copy(), f_min, f_max
    res = (f - f_min) * 255.0 / (f_max - f_min)
    return to_uint8(res), f_min, f_max


def equalize_gray(gray):
    """Эквализация (линейное выравнивание) по лекции:
    h -> нормализация h'(i)=h_i/H -> кумулятивная Sh(i) -> f' = 255 * Sh(f)."""
    h = histogram(gray).astype(np.float64)
    p = h / gray.size
    sh = np.cumsum(p)
    lut = np.clip(np.round(255.0 * sh), 0, 255).astype(np.uint8)
    return lut[gray]


def equalize_rgb(rgb):
    """Подход 1: эквализация каждой из компонент R, G, B по отдельности."""
    out = np.empty_like(rgb)
    for c in range(3):
        out[..., c] = equalize_gray(rgb[..., c])
    return out


def equalize_hsv(pil_rgb):
    """Подход 2: переход в HSV, эквализация только компоненты V, возврат в RGB."""
    h, s, v = pil_rgb.convert("HSV").split()
    v_eq = Image.fromarray(equalize_gray(np.array(v)))
    return Image.merge("HSV", (h, s, v_eq)).convert("RGB")


# ---------- Вспомогательное ----------
def luminance(pil_img):
    return np.array(pil_img.convert("L"))


def stats_text(pil_img):
    g = luminance(pil_img)
    return f"среднее={g.mean():.1f}  σ={g.std():.1f}  min={g.min()}  max={g.max()}"


def make_histogram_image(pil_img, width=266, height=110):
    """Гистограмма яркости (для цветного - три кривые R, G, B). 1 столбец = 1 уровень."""
    arr = np.array(pil_img)
    if arr.ndim == 2:
        chans = [(arr, (40, 40, 40))]
    else:
        chans = [(arr[..., 0], (220, 40, 40)),
                 (arr[..., 1], (30, 150, 30)),
                 (arr[..., 2], (40, 40, 220))]
    hists = [histogram(c) for c, _ in chans]
    max_val = max(int(h.max()) for h in hists)

    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (width - 1, height - 1)], outline=(180, 180, 180))
    if max_val == 0:
        return img
    margin = 5
    base = height - 4
    top_space = height - 10
    for (c, color), h in zip(chans, hists):
        if arr.ndim == 2:                                  # столбцы
            for x in range(256):
                hh = int(h[x] / max_val * top_space)
                if hh > 0:
                    draw.line([(margin + x, base), (margin + x, base - hh)], fill=color)
        else:                                              # ломаная
            pts = [(margin + x, base - int(h[x] / max_val * top_space)) for x in range(256)]
            draw.line(pts, fill=color, width=1)
    return img


def fit_image(pil_img, box):
    """Масштабирование с сохранением пропорций в квадрат box x box."""
    w, h = pil_img.size
    scale = min(box / w, box / h)
    new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
    return pil_img.resize(new_size, Image.NEAREST if scale > 1 else Image.LANCZOS)



SHARPEN_METHODS = [
    "Лапласиан 3x3 (отклик, контуры)",
    "LoG 5x5 (отклик, контуры)",
    "Градиент |Gx|+|Gy|",
    "Резкость: маска 3x3, центр 5",
    "Резкость: маска 3x3, центр 9",
    "Резкость: маска (1,-2,1), центр 5",
    "Резкость: маска 3x3, центр 20 (мягкая)",
    "Резкость: f + k * Лапласиан",
    "Нерезкое маскирование (Unsharp)",
]


class ImageProcessingApp:
    PREVIEW = 330

    def __init__(self, root):
        self.root = root
        self.root.title("Лабораторная работа №2 (Вариант 3)")

        self.img_orig = None     # исходное (RGB или L)
        self.img_rgb = None      # RGB-версия (если исходное цветное)
        self.img_gray = None     # полутоновая версия
        self.is_color = False
        self.img_proc = None

        ctrl = tk.Frame(root, padx=10, pady=4)
        ctrl.pack(side=tk.TOP, fill=tk.X)

        # --- Ряд 1: файл ---
        r1 = tk.Frame(ctrl)
        r1.pack(fill=tk.X, pady=2)
        tk.Button(r1, text="Открыть фото", command=self.load_image, bg="#d0e0f0").pack(side=tk.LEFT, padx=4)
        tk.Button(r1, text="Сохранить результат", command=self.save_result).pack(side=tk.LEFT, padx=4)
        tk.Button(r1, text="Сбросить", command=self.reset).pack(side=tk.LEFT, padx=4)

        # --- Ряд 2: контраст (полутона) ---
        r2 = tk.LabelFrame(ctrl, text="Повышение контраста (полутоновое изображение)")
        r2.pack(fill=tk.X, pady=3)
        tk.Button(r2, text="Линейное контрастирование", command=self.apply_linear).pack(side=tk.LEFT, padx=4, pady=2)
        tk.Label(r2, text="отсечение, %:").pack(side=tk.LEFT)
        self.clip_scale = tk.Scale(r2, from_=0.0, to=10.0, resolution=0.5, orient=tk.HORIZONTAL, length=90)
        self.clip_scale.set(0.0)
        self.clip_scale.pack(side=tk.LEFT)
        tk.Button(r2, text="Эквализация гистограммы", command=self.apply_equalize).pack(side=tk.LEFT, padx=4)
        tk.Button(r2, text="Сравнить: исходное / линейное / эквализация",
                  command=self.compare_contrast, bg="#f0e6c8").pack(side=tk.LEFT, padx=4)

        # --- Ряд 3: цвет ---
        r3 = tk.LabelFrame(ctrl, text="Эквализация цветного изображения")
        r3.pack(fill=tk.X, pady=3)
        tk.Button(r3, text="RGB (каждый канал)", command=self.apply_eq_rgb).pack(side=tk.LEFT, padx=4, pady=2)
        tk.Button(r3, text="HSV (только V)", command=self.apply_eq_hsv).pack(side=tk.LEFT, padx=4)
        tk.Button(r3, text="Сравнить: исходное / RGB / HSV",
                  command=self.compare_color, bg="#f0e6c8").pack(side=tk.LEFT, padx=4)

        # --- Ряд 4: ВЧ-фильтры ---
        r4 = tk.LabelFrame(ctrl, text="Высокочастотные фильтры (повышение резкости)")
        r4.pack(fill=tk.X, pady=3)
        self.method_box = ttk.Combobox(r4, values=SHARPEN_METHODS, state="readonly", width=38)
        self.method_box.current(3)
        self.method_box.pack(side=tk.LEFT, padx=4, pady=2)
        tk.Label(r4, text="k:").pack(side=tk.LEFT)
        self.k_scale = tk.Scale(r4, from_=0.1, to=5.0, resolution=0.1, orient=tk.HORIZONTAL, length=90)
        self.k_scale.set(1.0)
        self.k_scale.pack(side=tk.LEFT)
        tk.Label(r4, text="σ:").pack(side=tk.LEFT)
        self.sigma_scale = tk.Scale(r4, from_=0.5, to=5.0, resolution=0.1, orient=tk.HORIZONTAL, length=90)
        self.sigma_scale.set(1.5)
        self.sigma_scale.pack(side=tk.LEFT)
        tk.Button(r4, text="Применить", command=self.apply_sharpen, bg="#d0f0d0").pack(side=tk.LEFT, padx=4)
        tk.Button(r4, text="Сравнить фильтры", command=self.compare_sharpen, bg="#f0e6c8").pack(side=tk.LEFT, padx=4)

        # --- Информация ---
        self.info_label = tk.Label(root, text="Загрузите изображение для начала работы",
                                   font=("Arial", 11, "bold"), wraplength=960)
        self.info_label.pack(side=tk.TOP, pady=4)

        # --- Дисплей ---
        main = tk.Frame(root)
        main.pack(expand=True, fill=tk.BOTH, padx=10, pady=4)
        self.lbl_orig, self.lbl_hist_orig, self.lbl_stat_orig = self._make_block(main, "ИСХОДНОЕ ФОТО", tk.LEFT)
        self.lbl_proc, self.lbl_hist_proc, self.lbl_stat_proc = self._make_block(main, "РЕЗУЛЬТАТ", tk.RIGHT)

        self._fit_window(ctrl)

    def _fit_window(self, ctrl):
        """Подгоняет окно и размер превью под экран (с учётом масштаба Windows)."""
        self.root.update_idletasks()
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        avail_h = int(sh * 0.88)
        avail_w = int(sw * 0.96)
        lh = tkfont.Font(font=self.info_label.cget("font")).metrics("linespace")
        top_h = ctrl.winfo_reqheight() + self.info_label.winfo_reqheight() + 20
        overhead = 110 + 5 * lh + 50          # заголовок + подписи + гистограмма + статистика
        by_h = avail_h - top_h - overhead
        by_w = (avail_w - 80) // 2
        self.PREVIEW = int(max(120, min(330, by_h, by_w)))
        width = min(avail_w, max(ctrl.winfo_reqwidth() + 30, 2 * self.PREVIEW + 80))
        height = min(avail_h, top_h + overhead + self.PREVIEW)
        self.root.geometry(f"{int(width)}x{int(height)}+10+10")
        self.root.minsize(600, 400)

    def _make_block(self, parent, title, side):
        block = tk.Frame(parent, bd=1, relief=tk.SOLID)
        block.pack(side=side, expand=True, fill=tk.BOTH, padx=5)
        tk.Label(block, text=title, font=("Arial", 10, "bold")).pack(pady=2)
        lbl = tk.Label(block, text="Нет изображения", bg="#e0e0e0")
        lbl.pack(expand=True, fill=tk.BOTH, padx=5, pady=2)
        tk.Label(block, text="Гистограмма:", font=("Arial", 9)).pack(pady=(4, 0))
        hist = tk.Label(block, bg="#f5f5f5")
        hist.pack(pady=3)
        stat = tk.Label(block, text="", font=("Arial", 9))
        stat.pack(pady=(0, 4))
        return lbl, hist, stat

    # ------------------------------------------------------------------
    def _show(self, pil_img, lbl_img, lbl_hist, lbl_stat, attr):
        preview = fit_image(pil_img, self.PREVIEW)
        tk_img = ImageTk.PhotoImage(preview)
        lbl_img.config(image=tk_img, text="")
        hist = ImageTk.PhotoImage(make_histogram_image(pil_img))
        lbl_hist.config(image=hist)
        lbl_stat.config(text=stats_text(pil_img))
        setattr(self, attr, (tk_img, hist))   # держим ссылки, иначе Tk "потеряет" картинки

    def show_images(self):
        if self.img_orig is not None:
            self._show(self.img_orig, self.lbl_orig, self.lbl_hist_orig, self.lbl_stat_orig, "_refs_orig")
        if self.img_proc is not None:
            self._show(self.img_proc, self.lbl_proc, self.lbl_hist_proc, self.lbl_stat_proc, "_refs_proc")

    def _set_result(self, result, text):
        if isinstance(result, np.ndarray):
            result = Image.fromarray(result)
        self.img_proc = result
        self.show_images()
        self.info_label.config(text=text)

    def _need_image(self):
        if self.img_gray is None:
            self.info_label.config(text="Сначала откройте изображение")
            return False
        return True

    def _need_color(self):
        if not self._need_image():
            return False
        if not self.is_color:
            self.info_label.config(text="Изображение полутоновое: для сравнения RGB / HSV нужно цветное фото")
            return False
        return True

    # ------------------------------------------------------------------
    def load_image(self):
        path = filedialog.askopenfilename(filetypes=[("Изображения", "*.jpg *.jpeg *.png *.bmp *.tif *.tiff")])
        if not path:
            return
        img = Image.open(path).convert("RGB")
        arr = np.array(img)
        self.is_color = bool(np.any(arr[..., 0] != arr[..., 1]) or np.any(arr[..., 1] != arr[..., 2]))
        self.img_rgb = img
        self.img_gray = img.convert("L")
        self.img_orig = img if self.is_color else self.img_gray
        self.img_proc = self.img_orig.copy()
        self.show_images()
        kind = "цветное" if self.is_color else "полутоновое"
        self.info_label.config(text=f"Файл загружен ({kind}): {img.width}x{img.height} px")

    def reset(self):
        if self.img_orig is not None:
            self.img_proc = self.img_orig.copy()
            self.show_images()
            self.info_label.config(text="Результат сброшен к исходному изображению")

    def save_result(self):
        if self.img_proc is None:
            return
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if path:
            self.img_proc.save(path)
            self.info_label.config(text=f"Результат сохранён: {path}")

    # ------------------------------------------------------------------
    # 1. Контраст (над полутоновой версией)
    def apply_linear(self):
        if not self._need_image():
            return
        clip = float(self.clip_scale.get())
        res, f_min, f_max = linear_contrast(np.array(self.img_gray), clip)
        self._set_result(res, f"Линейное контрастирование: f_min={f_min:.0f}, f_max={f_max:.0f}"
                              f" -> [0, 255]" + (f" (отсечение {clip}%)" if clip > 0 else ""))

    def apply_equalize(self):
        if not self._need_image():
            return
        res = equalize_gray(np.array(self.img_gray))
        self._set_result(res, "Эквализация гистограммы: f' = 255 * Sh(f)")

    def compare_contrast(self):
        if not self._need_image():
            return
        g = np.array(self.img_gray)
        clip = float(self.clip_scale.get())
        lin, f_min, f_max = linear_contrast(g, clip)
        self.open_compare("Сравнение методов повышения контраста", [
            ("Исходное", self.img_gray),
            (f"Линейное контрастирование [{f_min:.0f}..{f_max:.0f}]", Image.fromarray(lin)),
            ("Эквализация гистограммы", Image.fromarray(equalize_gray(g))),
        ])

    # 2. Цветная эквализация
    def apply_eq_rgb(self):
        if not self._need_color():
            return
        res = equalize_rgb(np.array(self.img_rgb))
        self._set_result(Image.fromarray(res), "Эквализация в RGB: каждый канал отдельно (возможен сдвиг цветов)")

    def apply_eq_hsv(self):
        if not self._need_color():
            return
        self._set_result(equalize_hsv(self.img_rgb), "Эквализация в HSV: выравнивается только V (оттенок H и насыщенность S сохранены)")

    def compare_color(self):
        if not self._need_color():
            return
        self.open_compare("Сравнение эквализации цветного изображения", [
            ("Исходное", self.img_rgb),
            ("RGB: каждый канал", Image.fromarray(equalize_rgb(np.array(self.img_rgb)))),
            ("HSV: только V", equalize_hsv(self.img_rgb)),
        ])

    # 3. ВЧ-фильтры (над полутоновой версией)
    def _sharpen(self, gray, idx, k, sigma):
        if idx == 0:
            return laplace_response(gray, KERNEL_LAPLACE), "Лапласиан 3x3: L = f(x±1,y)+f(x,y±1)-4f (отклик +128)"
        if idx == 1:
            return laplace_response(gray, KERNEL_LOG), "Лапласиан гауссиана LoG 5x5 (отклик +128)"
        if idx == 2:
            return gradient_magnitude(gray), "Градиент: |Gx| + |Gy|"
        if idx == 3:
            return sharpen_mask(gray, KERNEL_SHARP_5), "Резкость: маска [0 -1 0; -1 5 -1; 0 -1 0]"
        if idx == 4:
            return sharpen_mask(gray, KERNEL_SHARP_9), "Резкость: маска [-1 -1 -1; -1 9 -1; -1 -1 -1]"
        if idx == 5:
            return sharpen_mask(gray, KERNEL_SHARP_121), "Резкость: маска [1 -2 1; -2 5 -2; 1 -2 1]"
        if idx == 6:
            return sharpen_mask(gray, KERNEL_SHARP_20), "Резкость: маска [0 -1 0; -1 20 -1; 0 -1 0], W=16 (мягкая)"
        if idx == 7:
            return sharpen_laplace_k(gray, k), f"Резкость: f + k*L(f), k = {k}"
        return unsharp_mask(gray, k, sigma), f"Нерезкое маскирование: f + k*(f - blur), k = {k}, σ = {sigma}"

    def apply_sharpen(self):
        if not self._need_image():
            return
        idx = self.method_box.current()
        k = float(self.k_scale.get())
        sigma = float(self.sigma_scale.get())
        res, text = self._sharpen(np.array(self.img_gray), idx, k, sigma)
        self._set_result(res, text)

    def compare_sharpen(self):
        if not self._need_image():
            return
        g = np.array(self.img_gray)
        k = float(self.k_scale.get())
        sigma = float(self.sigma_scale.get())
        items = [("Исходное", self.img_gray)]
        for idx, label in [(3, "Маска, центр 5"), (4, "Маска, центр 9"),
                           (7, f"f + k*L, k={k}"), (8, f"Unsharp k={k}, σ={sigma}")]:
            res, _ = self._sharpen(g, idx, k, sigma)
            items.append((label, Image.fromarray(res)))
        self.open_compare("Сравнение высокочастотных фильтров", items, thumb=230)

    # ------------------------------------------------------------------
    def open_compare(self, title, items, thumb=300):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.refs = []
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        thumb = int(max(100, min(thumb, (sw * 0.95) / len(items) - 30, sh * 0.88 - 260)))
        for col, (label, img) in enumerate(items):
            frame = tk.Frame(win, bd=1, relief=tk.SOLID)
            frame.grid(row=0, column=col, padx=4, pady=4, sticky="n")
            tk.Label(frame, text=label, font=("Arial", 9, "bold"), wraplength=thumb).pack(pady=2)
            tk_img = ImageTk.PhotoImage(fit_image(img, thumb))
            tk.Label(frame, image=tk_img).pack(padx=4)
            tk_hist = ImageTk.PhotoImage(make_histogram_image(img))
            tk.Label(frame, image=tk_hist).pack(pady=3)
            tk.Label(frame, text=stats_text(img), font=("Arial", 8)).pack(pady=(0, 4))
            win.refs.extend([tk_img, tk_hist])


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageProcessingApp(root)
    root.mainloop()