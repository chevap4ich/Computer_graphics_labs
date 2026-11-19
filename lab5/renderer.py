import ctypes
import random

import numpy as np
import pygame
from OpenGL.GL import *
from OpenGL.GLU import gluBuild2DMipmaps

from geometry import build_word, VERTEX_STRIDE


class Renderer:
    def __init__(self):
        # 1. Массив вершин слова + VBO.
        #    Формат вершины: x, y, z, u, v, nx, ny, nz
        self.vertices, self.vcount = build_word("БЕЛЯВСКИЙ")
        print(f"Массив вершин: {self.vcount} вершин, "
              f"{self.vertices.size} float, {self.vertices.nbytes} байт")

        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)

        # 2. Процедурная текстура (мелкие кирпичи)
        self.tex_id = self._make_brick_texture()

    def _make_brick_texture(self):
        size = 512
        cols, rows = 8, 16              # кирпичей в одной плитке по горизонтали / вертикали
        bw, bh = size // cols, size // rows
        mortar = 3                      # толщина шва в пикселях

        surf = pygame.Surface((size, size))
        surf.fill((190, 184, 174))      # раствор

        rnd = random.Random(7)          # фиксированное зерно - одинаковый вид при каждом запуске
        for r in range(rows):
            offset = bw // 2 if r % 2 else 0
            for c in range(-1, cols + 1):
                x = c * bw + offset
                y = r * bh
                k = rnd.randint(-14, 14)  # небольшой разброс оттенка
                color = (165 + k, 72 + k // 2, 52 + k // 3)
                pygame.draw.rect(surf, color,
                                 (x + mortar // 2, y + mortar // 2, bw - mortar, bh - mortar))

        tex_data = pygame.image.tostring(surf, "RGB", True)
        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        # Мипмапы - чтобы мелкие кирпичи не «рябили» при отдалении
        gluBuild2DMipmaps(GL_TEXTURE_2D, GL_RGB, size, size, GL_RGB, GL_UNSIGNED_BYTE, tex_data)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        return tex_id

    def setup_light(self):
        """Вызывать при единичной ModelView-матрице: источник света закреплён за камерой."""
        glLightfv(GL_LIGHT0, GL_POSITION, (0.4, 0.6, 1.0, 0.0))   # направленный свет
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.40, 0.40, 0.40, 1.0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.85, 0.85, 0.85, 1.0))
        glEnable(GL_LIGHT0)

    def draw(self):
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.tex_id)
        glEnable(GL_LIGHTING)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)
        glEnableClientState(GL_NORMAL_ARRAY)

        stride = VERTEX_STRIDE * 4
        glVertexPointer(3, GL_FLOAT, stride, ctypes.c_void_p(0))
        glTexCoordPointer(2, GL_FLOAT, stride, ctypes.c_void_p(3 * 4))
        glNormalPointer(GL_FLOAT, stride, ctypes.c_void_p(5 * 4))

        glColor3f(1.0, 1.0, 1.0)
        glDrawArrays(GL_TRIANGLES, 0, self.vcount)

        glDisableClientState(GL_VERTEX_ARRAY)
        glDisableClientState(GL_TEXTURE_COORD_ARRAY)
        glDisableClientState(GL_NORMAL_ARRAY)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glDisable(GL_COLOR_MATERIAL)
        glDisable(GL_LIGHTING)
        glDisable(GL_TEXTURE_2D)