import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

from renderer import draw_surname

def load_texture(filename):
    """Загрузка текстуры из файла средствами pygame и OpenGL."""
    try:
        texture_surface = pygame.image.load(filename)
    except pygame.error:
        print(f"Внимание: Файл текстуры {filename} не найден. Используется цветная заглушка.")
        return None

    texture_data = pygame.image.tostring(texture_surface, "RGBA", 1)
    width, height = texture_surface.get_rect().size

    tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    
    # Настройки фильтрации и повторения
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)

    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, texture_data)
    return tex_id

def main():
    surname = "БЕЛЯВСКИЙ"
    texture_path = "330px-Weathered_bricks_near_the_Albert_Dock.jpg"

    pygame.init()
    display = (1100, 650)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)

    # Загрузка текстуры
    texture_id = load_texture(texture_path)

    # буфер глубины
    glEnable(GL_DEPTH_TEST)
    glClearColor(0.08, 0.09, 0.12, 1.0)

    # проекция
    glMatrixMode(GL_PROJECTION)
    gluPerspective(45, (display[0] / display[1]), 0.1, 150.0)
    glMatrixMode(GL_MODELVIEW)

    # параметры камеры
    rot_x, rot_y = 15.0, -25.0
    zoom = -42.0
    clock = pygame.time.Clock()

    running = True
    frame_count = 0

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    zoom += 2.0
                elif event.button == 5:
                    zoom -= 2.0
            elif event.type == pygame.MOUSEMOTION:
                if pygame.mouse.get_pressed()[0]:
                    rot_y += event.rel[0] * 0.5
                    rot_x += event.rel[1] * 0.5

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        # --- ТРЕХМЕРНЫЕ ПРЕОБРАЗОВАНИЯ ---
        glTranslatef(0.0, 0.0, zoom)
        glRotatef(rot_x, 1, 0, 0)
        glRotatef(rot_y, 0, 1, 0)

        # Вывод матрицы
        # Получаем текущую матрицу ModelView (в ней уже учтены zoom, rot_x, rot_y)
        modelview_matrix = glGetFloatv(GL_MODELVIEW_MATRIX)
        
        if frame_count % 30 == 0:
            print("\n--- Текущая матрица преобразования (ModelView) ---")
            for row in modelview_matrix:
                print("[" + ", ".join(f"{val:8.4f}" for val in row) + "]")

        draw_surname(surname, texture_id)

        pygame.display.flip()
        clock.tick(60)
        frame_count += 1

    pygame.quit()

if __name__ == "__main__":
    main()