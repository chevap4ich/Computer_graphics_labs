import numpy as np
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from renderer import Renderer

WIDTH, HEIGHT = 1100, 650

# Начальные параметры камеры
START_ROT_X, START_ROT_Y = 15.0, -25.0
START_ZOOM = -11.0


def format_matrix(mat):
    """Форматирует матрицу ModelView в обычном математическом виде (строка i, столбец j).
    OpenGL хранит матрицу по столбцам, поэтому numpy-массив нужно транспонировать."""
    m = np.array(mat, dtype=float).T
    lines = []
    for i in range(4):
        lines.append("[ " + "  ".join(f"{m[i, j]:8.3f}" for j in range(4)) + " ]")
    return lines


def draw_hud(lines, font):
    """Рисует текст поверх 3D-сцены с помощью ортопроекции."""
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIDTH, HEIGHT, 0)  # начало координат - левый верхний угол

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    glEnable(GL_TEXTURE_2D)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    y_offset = 10
    for line in lines:
        surf = font.render(line, True, (200, 255, 200), (0, 0, 0))
        w, h = surf.get_size()
        # flipped=False: строки изображения идут сверху вниз, как и ось Y в нашей ортопроекции
        tex_data = pygame.image.tostring(surf, "RGBA", False)

        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, tex_data)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        glColor3f(1, 1, 1)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(10, y_offset)
        glTexCoord2f(1, 0); glVertex2f(10 + w, y_offset)
        glTexCoord2f(1, 1); glVertex2f(10 + w, y_offset + h)
        glTexCoord2f(0, 1); glVertex2f(10, y_offset + h)
        glEnd()

        glDeleteTextures([tex_id])
        y_offset += h + 2

    glDisable(GL_BLEND)
    glDisable(GL_TEXTURE_2D)
    glEnable(GL_DEPTH_TEST)

    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()


def main():
    pygame.init()
    pygame.display.set_caption("БЕЛЯВСКИЙ - 3D")
    pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)

    glEnable(GL_DEPTH_TEST)
    glClearColor(0.08, 0.09, 0.12, 1.0)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, WIDTH / HEIGHT, 0.1, 150.0)
    glMatrixMode(GL_MODELVIEW)

    renderer = Renderer()
    font = pygame.font.SysFont("consolas,dejavusansmono,couriernew,monospace", 15)

    rot_x, rot_y = START_ROT_X, START_ROT_Y
    zoom = START_ZOOM
    pan_x, pan_y = 0.0, 0.0
    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                rot_x, rot_y, zoom, pan_x, pan_y = START_ROT_X, START_ROT_Y, START_ZOOM, 0.0, 0.0
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    zoom = min(zoom + 1.0, -3.0)
                elif event.button == 5:
                    zoom = max(zoom - 1.0, -60.0)
            elif event.type == pygame.MOUSEMOTION:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                    if pygame.mouse.get_pressed()[0]:
                        pan_x += event.rel[0] * 0.02
                        pan_y -= event.rel[1] * 0.02
                elif pygame.mouse.get_pressed()[0]:
                    rot_y += event.rel[0] * 0.5
                    rot_x += event.rel[1] * 0.5

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        renderer.setup_light()   # свет привязан к камере

        # Трёхмерные преобразования: перенос (zoom + pan), затем повороты
        glTranslatef(pan_x, pan_y, zoom)
        glRotatef(rot_x, 1, 0, 0)
        glRotatef(rot_y, 0, 1, 0)

        # Итоговая матрица преобразования (ModelView)
        mat = glGetFloatv(GL_MODELVIEW_MATRIX)

        hud = ["Итоговая матрица преобразования:"]
        hud += format_matrix(mat)
        hud.append(f"rotX={rot_x:.1f}  rotY={rot_y:.1f}  "
                   f"pan=({pan_x:.2f}, {pan_y:.2f})  zoom={zoom:.1f}")
        hud.append("ЛКМ - вращение, Shift+ЛКМ - сдвиг, колесо - масштаб, R - сброс")

        renderer.draw()
        draw_hud(hud, font)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()