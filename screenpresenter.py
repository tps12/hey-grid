# coding: utf-8

from math import log10, sqrt
from random import randint, random

from PySide.QtCore import QPointF
from PySide.QtGui import QBrush, QColor, QFont, QGraphicsScene, QPen, QPolygonF, QWidgetItem

from grid import Grid
from griddetail import GridDetail
from hellogl import GLWidget

from colors import earth, gray, rgb

providers = sorted([m.Provider() for m in earth, gray, rgb], key=lambda p: p.name)

class ScreenPresenter(object):
    def __init__(self, view, uistack, widget):
        f = QFont('FreeMono')
        f.setWeight(QFont.Black)
        f.setPixelSize(16)

        self.grids = []
        self.colors = []

        self._view = view

        for p in providers:
            view.colors.addItem(p.name)
        view.colors.currentIndexChanged.connect(self.colorchange)

        self._detailview = view.detail
        self._detailview.scale(10, 10)

        self.add()

        view.layer.sliderMoved.connect(self.layer)
        view.detailLayer.sliderMoved.connect(self.detaillayer)

        self.detaillayer(-1)

        self._view.add.pressed.connect(self.add)

        widget.keyPressEvent = self.key

        view.rotation.valueChanged.connect(self.rotate)

        view.layer.setValue(view.layer.maximum())

        self._view.showDetail.pressed.connect(self.showdetail)
        self._view.hideDetail.pressed.connect(self.hidedetail)
        self.hidedetail()

        self._uistack = uistack

    def hidedetail(self):
        for i in range(self._view.grid.count()):
            item = self._view.grid.itemAt(i)
            if isinstance(item, QWidgetItem) and item.widget() is self._view.detailPanel:
                self._detailWidget = item.widget()
                self._detailPosition = self._view.grid.getItemPosition(i)
                self._detailWidget.setParent(None)
                break
        self._view.grid.setRowStretch(self._detailPosition[0], 0)
        self._view.hideDetail.setVisible(False)
        self._view.showDetail.setVisible(True)

    def showdetail(self):
        self._view.showDetail.setVisible(False)
        self._view.grid.addWidget(self._detailWidget, *self._detailPosition)
        self._view.grid.setRowStretch(self._detailPosition[0], 1)
        self._view.hideDetail.setVisible(True)

    def key(self, event):
        facecount = len(self._detail.grid.faces)
        try:
            direction = {
                u"'": 'NW',
                u',': 'N',
                u'.': 'NE',
                u'a': 'SW',
                u'o': 'S',
                u'e': 'SE'}[event.text()]
        except KeyError:
            direction = None
        if direction is not None:
            detail = self._detail.move(direction)
        else:
            try:
                rotation = {
                    u'\t': 'CCW',
                    u'p': 'CW'}[event.text()]
            except KeyError:
                rotation = None
            if rotation is not None:
                detail = self._detail.rotate(rotation)
            else:
                detail = self._detail
        self._detail = detail
        self._detailview.setScene(self._detail.scene)
        if len(self._detail.grid.faces) != facecount:
            for v in self._views:
                v.update()
                v.redraw()

    def colorchange(self, index):
        self.colors = [providers[index] for _ in self.grids]

        while self._view.angles.count() > 0:
            self._view.angles.takeAt(0).widget().deleteLater()
        self._views = [GLWidget(self.grids[-1], self.colors, offset, self._view, self._view.layer.value()) for offset in (0, 180)]
        for widget in self._views:
            self._view.angles.addWidget(widget)

        self.detaillayer(self._view.detailLayer.value())

    def add(self):
        self.grids.append(Grid(self.grids[-1]) if len(self.grids) > 0 else Grid())
        if self.grids[-1].prev is not None:
            if self._view.lazy.isChecked():
                self._view.lazy.setEnabled(False)
                self.grids[-1].populate(self.grids[-1].prev.faces.keys()[3])
            else:
                self.grids[-1].populate()

        for l in self._view.layer, self._view.detailLayer:
            l.setMaximum(self.grids[-1].size)
            if l.value() == self.grids[-1].size - 1:
                l.setValue(self.grids[-1].size)

        self.colorchange(providers.index(self.colors[0]) if len(self.colors) > 0 else 0)

    def layer(self, depth):
        for v in self._views:
            v.layer(depth)

    def prefix(self, order):
        prefices = [
            (-9, u'n'),
            (-6, u'µ'),
            (-3, u'm'),
            (-2, u'c'),
            (0, None),
            (3, u'k')
        ]
        if order <= prefices[0][0]:
            return order - prefices[0][0], prefices[0][1]
        if order >= prefices[-1][0]:
            return order - prefices[-1][0], prefices[-1][1]
        for i in range(1, len(prefices)):
            if order < prefices[i][0]:
                return order - prefices[i-1][0], prefices[i-1][1]

    def labelscale(self, order, unit):
        offset, prefix = self.prefix(order)
        return u'{:,}{}{}'.format(pow(10, offset), prefix if prefix is not None else u'', unit)

    def scale(self, grid, radius, unit):
        dth = grid.scale()
        ds = radius * grid.scale()
        order = int(round(log10(ds)))
        if pow(10, order) / ds > 1.125:
            order -= 1
        dth = pow(10, order) / ds
        label1, label10 = [self.labelscale(o, unit) for o in (order, order+1)]
        return dth, label1, label10

    def detaillayer(self, depth):
        self._detail = GridDetail(self.grids[depth], self.colors[depth], self.grids[depth].faces.keys()[0], ((0,-1,0), u'N'), self.scale(self.grids[depth], 6371000, u'm'))
        self._detailview.setScene(self._detail.scene)

    def rotate(self, value):
        for v in self._views:
            v.rotate(value)
