# coding: utf-8

from math import sqrt

from PySide.QtGui import QColor, QFontMetrics, QPen

from common import N, NW, NE, S, SE, SW, offsets

class Legend(object):
    def __init__(self, scene, font, poiinfo, scaleinfo):
        poi = self._labelpointofinterest(scene, font, *poiinfo)
        offset = max([item.boundingRect().height() for item in poi])
        scale = self._labelscale(scene, font, offset, *scaleinfo)

        self.group = scene.createItemGroup(poi + scale)

    def _labelpointofinterest(self, scene, font, poidirection, poilabel, poimark):
        label = self._addtext(scene, font, poilabel + u' ', (0, 0), 0)
        if poidirection is None:
            poidirection = 0
        else:
            poimark = u'↑'
        key = self._addtext(scene, font, poimark, (label.boundingRect().width() * 0.2, 0), poidirection)
        return [label, key]

    def _color(self):
        return QColor(255, 255, 255)

    def _labelscale(self, scene, font, offset, scalelen, label1, label10):
        metrics = QFontMetrics(font)

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

        text = self._addtext(scene, font, label1, (0, offset * 0.2), 0)
        text10 = self._addtext(scene, font, label10, (0, offset * 0.2), 0)

        x1 = 5 * w - metrics.width(label1) * 0.1
        x10 = 50 * w - metrics.width(label10) * 0.1
        overlap = x1 + text10.boundingRect().width() - x10
        if overlap > 0:
            x1 -= overlap/2
            x10 += overlap/2

        text.translate(x1, y + h + metrics.height())
        text10.translate(x10, y + h + metrics.height())

        return [text, text10] + lines

    def _addtext(self, scene, font, content, offset, rotation):
        text = scene.addText(content, font)
        text.setDefaultTextColor(self._color())
        metrics = QFontMetrics(font)
        text.translate(offset[0] - 2, offset[1] - sqrt(3)/2 - metrics.height() * 0.1)
        text.scale(0.2, 0.2)
        text.setTransformOriginPoint(*text.boundingRect().center().toTuple())
        text.setRotation(rotation)
        return text
