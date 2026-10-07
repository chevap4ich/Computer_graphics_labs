import tkinter as tk
from tkinter import colorchooser

# ограничения значений
def clamp(v, lo, hi):
    return max(lo, min(hi, int(v)))


# rgb в cmyk
def rgb_to_cmyk(r, g, b):
    r, g, b = r / 255, g / 255, b / 255
    k = 1 - max(r, g, b)
    if k >= 1:
        return 0, 0, 0, 100
    c = (1 - r - k) / (1 - k)
    m = (1 - g - k) / (1 - k)
    y = (1 - b - k) / (1 - k)
    return round(c * 100), round(m * 100), round(y * 100), round(k * 100)


# cmyk в rgb
def cmyk_to_rgb(c, m, y, k):
    c, m, y, k = c / 100, m / 100, y / 100, k / 100
    r = 255 * (1 - c) * (1 - k)
    g = 255 * (1 - m) * (1 - k)
    b = 255 * (1 - y) * (1 - k)
    return round(r), round(g), round(b)


# перевод тона в компоненту rgb
def hue_to_rgb(p, q, t):
    if t < 0: t += 1
    if t > 1: t -= 1
    if t < 1 / 6: return p + (q - p) * 6 * t
    if t < 1 / 2: return q
    if t < 2 / 3: return p + (q - p) * (2 / 3 - t) * 6
    return p


# rgb в hls
def rgb_to_hls(r, g, b):
    r, g, b = r / 255, g / 255, b / 255
    mx, mn = max(r, g, b), min(r, g, b)
    l = (mx + mn) / 2
    if mx == mn:
        h = 0
        s = 0
    else:
        d = mx - mn
        s = d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)
        if mx == r:
            h = (60 * ((g - b) / d)) % 360
        elif mx == g:
            h = 60 * ((b - r) / d + 2)
        else:
            h = 60 * ((r - g) / d + 4)
    return round(h), round(l * 100), round(s * 100)


# hls в rgb
def hls_to_rgb(h, l, s):
    l, s = l / 100, s / 100
    if s == 0:
        v = round(l * 255)
        return v, v, v
    q = l * (1 + s) if l < 0.5 else l + s - l * s
    p = 2 * l - q
    hk = h / 360
    r = hue_to_rgb(p, q, hk + 1 / 3)
    g = hue_to_rgb(p, q, hk)
    b = hue_to_rgb(p, q, hk - 1 / 3)
    return round(r * 255), round(g * 255), round(b * 255)


class ColorApp:
    def __init__(self, root):
        self.root = root
        root.title("Цветовые модели: RGB / CMYK / HLS")

        self.updating = False

        self.preview = tk.Canvas(root, width=460, height=80,
                                 highlightthickness=1, highlightbackground="black")
        self.preview.pack(padx=10, pady=10, fill="x")

        tk.Button(root, text="Выбрать цвет из палитры",
                  command=self.pick_from_palette).pack(pady=4)

        self.rgb_vars = [tk.IntVar(value=255), tk.IntVar(value=0), tk.IntVar(value=0)]
        self.cmyk_vars = [tk.IntVar(value=0), tk.IntVar(value=100),
                          tk.IntVar(value=100), tk.IntVar(value=0)]
        self.hls_vars = [tk.IntVar(value=0), tk.IntVar(value=50), tk.IntVar(value=100)]

        f = tk.LabelFrame(root, text="RGB (0-255)")
        f.pack(fill="x", padx=10, pady=4)
        for i, name in enumerate("RGB"):
            self.make_row(f, name, self.rgb_vars[i], 0, 255, "rgb")

        f = tk.LabelFrame(root, text="CMYK (0-100 %)")
        f.pack(fill="x", padx=10, pady=4)
        for i, name in enumerate(["C", "M", "Y", "K"]):
            self.make_row(f, name, self.cmyk_vars[i], 0, 100, "cmyk")

        f = tk.LabelFrame(root, text="HLS (H:0-360, L/S:0-100 %)")
        f.pack(fill="x", padx=10, pady=4)
        for i, (name, hi) in enumerate(zip(["H", "L", "S"], [360, 100, 100])):
            self.make_row(f, name, self.hls_vars[i], 0, hi, "hls")

        self.update_all("rgb")

    def make_row(self, parent, label, var, lo, hi, model):
        row = tk.Frame(parent)
        row.pack(fill="x", padx=4, pady=2)
        tk.Label(row, text=label, width=2).pack(side="left")
        # ползунок
        tk.Scale(row, from_=lo, to=hi, orient="horizontal", variable=var,
                 showvalue=0,
                 command=lambda _v: self.on_user_change(model)).pack(
            side="left", fill="x", expand=True)
        en = tk.Entry(row, width=6, textvariable=var)
        en.pack(side="left", padx=4)
        en.bind("<Return>", lambda _e: self.on_user_change(model))
        en.bind("<FocusOut>", lambda _e: self.on_user_change(model))

    def on_user_change(self, model):
        if self.updating:
            return
        self.update_all(model)

    def update_all(self, source):
        self.updating = True

        if source == "rgb":
            r, g, b = (clamp(v.get(), 0, 255) for v in self.rgb_vars)
        elif source == "cmyk":
            c, m, y, k = (clamp(v.get(), 0, 100) for v in self.cmyk_vars)
            r, g, b = cmyk_to_rgb(c, m, y, k)
        else:  # hls
            h = clamp(self.hls_vars[0].get(), 0, 360)
            l = clamp(self.hls_vars[1].get(), 0, 100)
            s = clamp(self.hls_vars[2].get(), 0, 100)
            r, g, b = hls_to_rgb(h, l, s)

        if source != "rgb":
            for var, val in zip(self.rgb_vars, (r, g, b)):
                var.set(val)

        if source != "cmyk":
            for var, val in zip(self.cmyk_vars, rgb_to_cmyk(r, g, b)):
                var.set(val)

        if source != "hls":
            for var, val in zip(self.hls_vars, rgb_to_hls(r, g, b)):
                var.set(val)

        self.preview.config(bg="#%02x%02x%02x" % (r, g, b))

        self.updating = False

    def pick_from_palette(self):
        r, g, b = (v.get() for v in self.rgb_vars)
        rgb, _ = colorchooser.askcolor(initialcolor="#%02x%02x%02x" % (r, g, b))
        if rgb is None:
            return
        self.updating = True
        for var, val in zip(self.rgb_vars, map(int, rgb)):
            var.set(val)
        self.updating = False
        self.update_all("rgb")


if __name__ == "__main__":
    root = tk.Tk()
    app = ColorApp(root)
    root.mainloop()