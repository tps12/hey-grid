from math import sqrt
from random import randint, random

from PySide.QtCore import QPointF
from PySide.QtGui import QBrush, QColor, QFont, QGraphicsScene, QPen, QPolygonF

from grid import Grid
from griddetail import GridDetail
from hellogl import GLWidget

class ScreenPresenter(object):
    def __init__(self, view, uistack, widget):
        f = QFont('FreeMono')
        f.setWeight(QFont.Black)
        f.setPixelSize(16)

        grid = Grid()
        while grid.size < 3:
            subgrid = Grid(grid)
            subgrid.populate()
            grid = subgrid
        p = grid.faces.keys()[12]
        subgrid = Grid(grid)
        subgrid.populate(p)
        grid = subgrid
        while grid.size < 7:
            subgrid = Grid(grid)
            subgrid.populate(grid.faces.keys()[3])
            grid = subgrid

        grids = []
        prev = grid
        while prev is not None:
            grids.insert(0, prev)
            prev = prev.prev
        colors = [{}]
        for f in grids[0].faces:
            colors[-1][f] = tuple(3 * [0.5 * random() + 0.25])
        for g in grids[1:]:
            colors.append({})
            for f in g.faces:
                if f in g.prev.faces:
                    colors[-1][f] = colors[-2][f]
                else:
                    cs = [colors[-2][n][0] for n in g.prev.vertices[f] if n in colors[-2]]
                    colors[-1][f] = tuple(3 * [sum(cs)/len(cs) + 0.125 * random() - 0.0675])

        self._views = [GLWidget(grid, colors, 0, view), GLWidget(grid, colors, 180, view)]
        for v in self._views:
            view.angles.addWidget(v)

        for face in grids[0].faces.keys():
            if len(grids[0].faces[face]) == 6:
                break
        self._detail = GridDetail(grids, colors, face)
        view.detail.setScene(self._detail)
        view.detail.scale(10, -10)

        view.layer.sliderMoved.connect(self.layer)
        view.detailLayer.sliderMoved.connect(self.detaillayer)

        for l in view.layer, view.detailLayer:
            l.setMaximum(grid.size)
            l.setValue(grid.size)

        view.rotation.valueChanged.connect(self.rotate)

        view.layer.setValue(view.layer.maximum())

        self._uistack = uistack

    def layer(self, depth):
        for v in self._views:
            v.layer(depth)

    def detaillayer(self, depth):
        self._detail.layer(depth)

    def rotate(self, value):
        for v in self._views:
            v.rotate(value)
