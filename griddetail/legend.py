# coding: utf-8

from math import sqrt

from PySide.QtGui import QColor, QFontMetrics, QPen

N, NW, SW, S, SE, NE = range(6)
offsets = [(0, -2*sqrt(3)), (-3, -sqrt(3)), (-3, sqrt(3)), (0, 2*sqrt(3)), (3, sqrt(3)), (3, -sqrt(3))]

class Legend(object):
    def __init__(self, scene, poiinfo, scaleinfo):
        poi = self._labelpointofinterest(scene, *poiinfo)
        offset = max([item.boundingRect().height() for item in poi])
        scale = self._labelscale(scene, offset, *scaleinfo)

        self.group = scene.createItemGroup(poi + scale)

    def _labelpointofinterest(self, scene, poidirection, poilabel, poimark):
        label = self._addtext(scene, poilabel + u' ', (0, 0), 0)
        if poidirection is None:
            poidirection = 0
        else:
            poimark = u'↑'
        key = self._addtext(scene, poimark, (label.boundingRect().width() * 0.2, 0), poidirection)
        return [label, key]

    def _color(self):
        return QColor(255, 255, 255)

    def _labelscale(self, scene, offset, scalelen, label1, label10):
        text = self._addtext(scene, label1, (0, offset * 0.2), 0)
        metrics = QFontMetrics(text.font())

        pen = QPen(self._color())
        y = offset * 0.2
        w = scalelen * abs(offsets[N][1])
        h = metrics.height() * 0.2

        lines = []
        lines.append(scene.addLine(0, y, 0, y + h, pen))
        lines.append(scene.addLine(0, y + h, w, y + h, pen))
        lines.append(scene.addLine(w, y + h, w, y + h/2.0, pen))

        lines.append(scene.addLine(w, y + h, 10 * w, y + h, pen))
        lines.append(scene.addLine(10 * w, y + h, 10 * w, y, pen))

        text10 = self._addtext(scene, label10, (0, offset * 0.2), 0)

        x1 = 5 * w - metrics.width(label1) * 0.1
        x10 = 50 * w - metrics.width(label10) * 0.1
        overlap = x1 + text10.boundingRect().width() - x10
        if overlap > 0:
            x1 -= overlap/2
            x10 += overlap/2

        text.translate(x1, y + h + metrics.height())
        text10.translate(x10, y + h + metrics.height())

        return [text, text10] + lines

    def _addtext(self, scene, content, offset, rotation):
        text = scene.addText(content)
        text.setDefaultTextColor(self._color())
        metrics = QFontMetrics(text.font())
        text.translate(offset[0] - 2, offset[1] - sqrt(3)/2 - metrics.height() * 0.1)
        text.scale(0.2, 0.2)
        text.setTransformOriginPoint(*text.boundingRect().center().toTuple())
        text.setRotation(rotation)
        return text
