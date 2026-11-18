from letters import LETTERS

def build_word_cubes(word, letter_width=6.0):
    total_width = len(word) * letter_width - 1.0
    start_x = -total_width / 2.0
    cubes = []

    for char_idx, char in enumerate(word):
        grid = LETTERS.get(char.upper())
        if not grid:
            continue
            
        for row_idx, row in enumerate(grid):
            for col_idx, cell in enumerate(row):
                if cell == '#':
                    x = start_x + char_idx * letter_width + col_idx
                    y = 2.0 - row_idx
                    cubes.append((x, y, 0.0))

    return cubes