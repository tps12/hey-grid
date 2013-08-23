from math import sqrt
from random import randint

from PySide.QtCore import QPointF
from PySide.QtGui import QBrush, QColor, QFont, QGraphicsScene, QPen, QPolygonF

from hellogl import GLWidget, Grid, SubGrid

class ScreenPresenter(object):
    def __init__(self, view, uistack, widget):
        f = QFont('FreeMono')
        f.setWeight(QFont.Black)
        f.setPixelSize(16)

        grid = Grid.grid(2)
        p = grid.faces.keys()[12]
        subgrid = SubGrid(grid)
        subgrid.populate(p)
        grid = subgrid
        while grid.size < 7:
            subgrid = SubGrid(grid)
            subgrid.populate(grid.faces.keys()[3])
            grid = subgrid

        self._views = [GLWidget(grid, 0, view), GLWidget(grid, 180, view)]
        for v in self._views:
            view.angles.addWidget(v)

        view.layer.setMaximum(grid.size)

        view.layer.sliderMoved.connect(self.layer)
        view.rotation.valueChanged.connect(self.rotate)

        view.layer.setValue(view.layer.maximum())

        self._uistack = uistack

    def layer(self, depth):
        for v in self._views:
            v.layer(depth)

    def rotate(self, value):
        for v in self._views:
            v.rotate(value)
