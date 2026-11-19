import math
import numpy as np

# Параметры шрифта (в условных единицах сцены)
HEIGHT = 1.5      # высота заглавной буквы
DEPTH = 0.5       # толщина (глубина выдавливания) буквы по оси Z
THICK = 0.22      # толщина штриха
GAP = 0.3         # расстояние между буквами
WIDTH = 0.9       # ширина буквы

# Сколько единиц сцены занимает одна «плитка» текстуры (чем меньше - тем мельче кирпичи)
TEX_SCALE = 3.0

# Формат одной вершины в итоговом массиве: x, y, z, u, v, nx, ny, nz
VERTEX_STRIDE = 8

# Базовые примитивы: каждый примитив - массив вершин выпуклого 2D-полигона

def rect(x0, y0, x1, y1):
    """Прямоугольник: 4 вершины (против часовой стрелки)."""
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def slant(xb, xt, y0, y1, t):
    """Наклонный штрих (параллелограмм с горизонтальными торцами).
    xb - x центра штриха внизу (на y0), xt - x центра штриха вверху (на y1)."""
    return [[xb - t / 2, y0], [xb + t / 2, y0], [xt + t / 2, y1], [xt - t / 2, y1]]



# Контуры букв, для каждой буквы - список выпуклых полигонов,

def letter_B():  # Б
    H, T, W = HEIGHT, THICK, WIDTH
    yb = H * 0.58  # верх нижней «чаши»
    return [
        rect(0, 0, T, H),                 # левая вертикаль
        rect(0, H - T, W, H),             # верхняя перекладина
        rect(0, yb - T, W, yb),           # перекладина над чашей
        rect(0, 0, W, T),                 # нижняя перекладина
        rect(W - T, 0, W, yb),            # правая стенка чаши
    ]


def letter_E():  # Е
    H, T, W = HEIGHT, THICK, WIDTH
    return [
        rect(0, 0, T, H),
        rect(0, H - T, W, H),
        rect(0, H / 2 - T / 2, W * 0.88, H / 2 + T / 2),
        rect(0, 0, W, T),
    ]


def letter_L():  # Л
    H, T, W = HEIGHT, THICK, WIDTH
    return [
        rect(0.26, H - T, W, H),                 # верхняя перекладина
        rect(W - T, 0, W, H),                    # правая вертикаль
        slant(0.14, 0.38, 0, H, T * 1.1),        # левая наклонная нога
    ]


def letter_Ya():  # Я
    H, T, W = HEIGHT, THICK, WIDTH
    ym = H * 0.46
    return [
        rect(W - T, 0, W, H),                    # правая вертикаль
        rect(0, H - T, W, H),                    # верх чаши
        rect(0, ym - T / 2, W, ym + T / 2),      # низ чаши
        rect(0, ym - T / 2, T, H),               # левая стенка чаши
        slant(0.12, 0.60, 0, ym, T * 1.1),       # нога
    ]


def letter_V():  # В
    H, T, W = HEIGHT, THICK, WIDTH
    ym = H / 2
    wt = W - 0.08  # верхняя чаша чуть уже нижней
    return [
        rect(0, 0, T, H),                        # левая вертикаль
        rect(0, H - T, wt, H),                   # верхняя перекладина
        rect(0, ym - T / 2, W - T, ym + T / 2),  # средняя перекладина
        rect(0, 0, W, T),                        # нижняя перекладина
        rect(wt - T, ym - T / 2, wt, H),         # правая стенка верхней чаши
        rect(W - T, 0, W, ym + T / 2),           # правая стенка нижней чаши
    ]


def letter_S():  # С
    H, T, W = HEIGHT, THICK, WIDTH
    return [
        rect(0, 0, T, H),                        # левая вертикаль
        rect(0, H - T, W, H),                    # верх
        rect(0, 0, W, T),                        # низ
        rect(W - T, H - 0.45, W, H),             # верхний «носик»
        rect(W - T, 0, W, 0.45),                 # нижний «носик»
    ]


def letter_K():  # К
    H, T, W = HEIGHT, THICK, WIDTH
    ym = H / 2
    return [
        rect(0, 0, T, H),                              # вертикаль
        slant(0.30, W - 0.11, ym - 0.05, H, T * 1.1),  # верхняя ветвь
        slant(W - 0.11, 0.40, 0, ym + 0.1, T * 1.1),   # нижняя ветвь
    ]


def letter_I():  # И
    H, T, W = HEIGHT, THICK, WIDTH
    return [
        rect(0, 0, T, H),
        rect(W - T, 0, W, H),
        slant(0.20, W - 0.20, 0, H, T * 1.1),    # диагональ снизу-слева вверх-вправо
    ]


def letter_I_short():  # Й
    H, T, W = HEIGHT, THICK, WIDTH
    polys = letter_I()
    # «галочка» над буквой
    polys += [
        slant(0.40, 0.25, H + 0.10, H + 0.30, 0.10),
        slant(0.50, 0.65, H + 0.10, H + 0.30, 0.10),
        rect(0.35, H + 0.10, 0.55, H + 0.19),
    ]
    return polys


# Словарь: символ -> {ширина, массив полигонов}
WORD_MAP = {
    'Б': {'w': WIDTH, 'polys': letter_B()},
    'Е': {'w': WIDTH, 'polys': letter_E()},
    'Л': {'w': WIDTH, 'polys': letter_L()},
    'Я': {'w': WIDTH, 'polys': letter_Ya()},
    'В': {'w': WIDTH, 'polys': letter_V()},
    'С': {'w': WIDTH, 'polys': letter_S()},
    'К': {'w': WIDTH, 'polys': letter_K()},
    'И': {'w': WIDTH, 'polys': letter_I()},
    'Й': {'w': WIDTH, 'polys': letter_I_short()},
}

# Выдавливание 2D-полигона в 3D-призму
def add_prism(p, verts, x_offset):
    """Превращает 2D-полигон в призму и дописывает вершины в массив verts.
    Каждая вершина: x, y, z, u, v, nx, ny, nz."""
    # Гарантируем обход против часовой стрелки
    area = sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1]
               for i in range(len(p))) / 2
    if area < 0:
        p = p[::-1]

    z1, z0 = DEPTH / 2, -DEPTH / 2
    n = len(p)

    def add(x, y, z, u, v, nx, ny, nz):
        verts.extend([x + x_offset, y, z, u, v, nx, ny, nz])

    # Передняя грань (веер треугольников). UV зависят от положения в мире,
    # поэтому кирпичная кладка непрерывна даже там, где призмы пересекаются.
    for i in range(1, n - 1):
        for k in (0, i, i + 1):
            x, y = p[k]
            add(x, y, z1, (x + x_offset) / TEX_SCALE, y / TEX_SCALE, 0, 0, 1)

    # Задняя грань (обратный обход)
    for i in range(1, n - 1):
        for k in (0, i + 1, i):
            x, y = p[k]
            add(x, y, z0, (x + x_offset) / TEX_SCALE, y / TEX_SCALE, 0, 0, -1)

    # Боковые грани
    acc = 0.0
    vf = DEPTH / TEX_SCALE
    for i in range(n):
        a, b = p[i], p[(i + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy)
        if length < 1e-9:
            continue
        nx, ny = dy / length, -dx / length  # внешняя нормаль для обхода против часовой
        ua, ub = acc / TEX_SCALE, (acc + length) / TEX_SCALE
        acc += length

        add(a[0], a[1], z0, ua, 0, nx, ny, 0)
        add(b[0], b[1], z0, ub, 0, nx, ny, 0)
        add(b[0], b[1], z1, ub, vf, nx, ny, 0)

        add(a[0], a[1], z0, ua, 0, nx, ny, 0)
        add(b[0], b[1], z1, ub, vf, nx, ny, 0)
        add(a[0], a[1], z1, ua, vf, nx, ny, 0)


def build_word(word):
    """Собирает единый МАССИВ ВЕРШИН для всего слова.
    Возвращает (numpy-массив float32 формы (N, 8), количество вершин N)."""
    verts = []
    total_width = sum(WORD_MAP[c]['w'] for c in word) + GAP * (len(word) - 1)
    x0 = -total_width / 2.0

    for char in word:
        letter = WORD_MAP[char]
        for poly in letter['polys']:
            # Сдвигаем по Y, чтобы слово было по центру
            shifted = [[q[0], q[1] - HEIGHT / 2] for q in poly]
            add_prism(shifted, verts, x0)
        x0 += letter['w'] + GAP

    arr = np.array(verts, dtype=np.float32).reshape(-1, VERTEX_STRIDE)
    return arr, len(arr)