from OpenGL.GL import *
from word_builder import build_word_cubes

VERTICES = (
    ( 0.5, -0.5, -0.5), ( 0.5,  0.5, -0.5),
    (-0.5,  0.5, -0.5), (-0.5, -0.5, -0.5),
    ( 0.5, -0.5,  0.5), ( 0.5,  0.5,  0.5),
    (-0.5, -0.5,  0.5), (-0.5,  0.5,  0.5)
)

SURFACES = (
    (0, 1, 2, 3), (3, 2, 7, 6), (6, 7, 5, 4),
    (4, 5, 1, 0), (1, 5, 7, 2), (4, 0, 3, 6)
)

EDGES = (
    (0, 1), (1, 2), (2, 3), (3, 0),
    (4, 5), (5, 7), (7, 6), (6, 4),
    (0, 4), (1, 5), (2, 7), (3, 6)
)

TEX_COORDS = (
    (0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0)
)

def draw_cube(x, y, z, texture_id=None):
    glPushMatrix()
    glTranslatef(x, y, z)

    if texture_id is not None:
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glColor3f(1.0, 1.0, 1.0) # Белый цвет: текстура без искажений
    else:
        glDisable(GL_TEXTURE_2D)

    # Грани
    glBegin(GL_QUADS)
    for surface in SURFACES:
        if texture_id is None:
            glColor3f(0.3, 0.5, 0.8) # Однотонный цвет, если текстуры нет
            
        for j, vertex in enumerate(surface):
            if texture_id is not None:
                glTexCoord2fv(TEX_COORDS[j])
            glVertex3fv(VERTICES[vertex])
    glEnd()

    # Ребра
    glDisable(GL_TEXTURE_2D)
    glColor3f(0.05, 0.05, 0.1)
    glLineWidth(1.5)
    glBegin(GL_LINES)
    for edge in EDGES:
        for vertex in edge:
            glVertex3fv(VERTICES[vertex])
    glEnd()

    glPopMatrix()

def draw_word(cubes, texture_id=None):
    for x, y, z in cubes:
        draw_cube(x, y, z, texture_id)

def draw_surname(word, texture_id=None):
    cubes = build_word_cubes(word)
    draw_word(cubes, texture_id)