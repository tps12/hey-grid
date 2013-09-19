from math import sqrt

N, NW, SW, S, SE, NE = range(6)
dirs = ['N', 'NW', 'SW', 'S', 'SE', 'NE']
offsets = [(0, -2*sqrt(3)), (-3, -sqrt(3)), (-3, sqrt(3)), (0, 2*sqrt(3)), (3, sqrt(3)), (3, -sqrt(3))]

def rotatedirection(direction, steps):
    return (direction + steps) % 6

def borders(grid, face, direction, edge):
    # edges are in CCW order: find edge of origin in list to orient
    count = 0
    for border in grid.borders(face, edge):
        yield (rotatedirection(direction, count + 1), border)
        count += 1
