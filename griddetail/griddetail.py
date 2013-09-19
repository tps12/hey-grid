# coding: utf-8

from PySide.QtGui import QGraphicsScene

from hexgrid import HexGrid
from legend import Legend

N, NW, SW, S, SE, NE = range(6)
dirs = ['N', 'NW', 'SW', 'S', 'SE', 'NE']

def rotatedirection(direction, steps):
    return (direction + steps) % 6

def borders(grid, face, direction, edge):
    # edges are in CCW order: find edge of origin in list to orient
    count = 0
    for border in grid.borders(face, edge):
        yield (rotatedirection(direction, count + 1), border)
        count += 1

class GridDetail(object):
    def __init__(self, grid, colors, center, (poilocation, poilabel), scale, orientation=None):
        self.scene = QGraphicsScene()

        self.grid = grid
        self.colors = colors

        self._center = center

        self._pointofinterest = (poilocation, poilabel)
        self._scale = scale

        # default to arbitrarily chosen local North edge
        self._orientation = (S, tuple(sorted(grid.faces[center][0:2]))) if orientation is None else orientation

        poimark = u'★'
        hexgrid = HexGrid(self.scene, self.grid, self.colors, self._center, self._orientation, (poilocation, poimark))
        legend = Legend(self.scene, (hexgrid.poidirection, poilabel, poimark), scale)

        self._groups = [obj.group for obj in hexgrid, legend]
        gridsize, legendsize = [group.boundingRect() for group in self._groups]
        self._groups[-1].translate(gridsize.x() - legendsize.width()/2, gridsize.y() + gridsize.height() + legendsize.height()/2)
        self._groups[-1].setZValue(1)

    def move(self, direction):
        orientation = self._orientation
        for nextdir, border in borders(self.grid, self._center, *orientation):
            if nextdir == dirs.index(direction):
                face = self.grid.neighbor(self._center, border)
                break
        else:
            face = self.grid.neighbor(self._center, orientation[1])
        edge = list(set(self.grid.edges(self._center)) & set(self.grid.edges(face)))[0]
        return GridDetail(self.grid, self.colors, face, self._pointofinterest, self._scale, ((dirs.index(direction) + 3) % 6, edge))

    def rotate(self, rotation):
        change = 1 if rotation == 'CW' else -1
        direction, edge = self._orientation
        return GridDetail(self.grid, self.colors, self._center, self._pointofinterest, self._scale, (direction + change, edge))
