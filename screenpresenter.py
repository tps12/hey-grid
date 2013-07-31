from math import sqrt
from random import randint

from PySide.QtCore import QPointF
from PySide.QtGui import QBrush, QColor, QFont, QGraphicsScene, QPen, QPolygonF

from hellogl import GLWidget, Grid

class ScreenPresenter(object):
    def __init__(self, view, uistack, widget):
        f = QFont('FreeMono')
        f.setWeight(QFont.Black)
        f.setPixelSize(16)

        view.rotation.valueChanged.connect(self.rotate)

        grid = Grid.grid(2)
        self._views = [GLWidget(grid, 0, view), GLWidget(grid, 180, view)]
        for v in self._views:
            view.angles.addWidget(v)

        self._uistack = uistack

    def rotate(self, value):
		for v in self._views:
			v.rotate(value)
