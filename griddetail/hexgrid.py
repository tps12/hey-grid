# coding: utf-8

from math import acos, atan2, pi, sqrt

from PySide.QtCore import QPointF, Qt
from PySide.QtGui import QColor, QFontMetrics, QMatrix, QPen, QPolygonF

N, NW, SW, S, SE, NE = range(6)
dirs = ['N', 'NW', 'SW', 'S', 'SE', 'NE']
vs = [(-1, -sqrt(3)), (1, -sqrt(3)), (2, 0), (1, sqrt(3)), (-1, sqrt(3)), (-2, 0)]
offsets = [(0, -2*sqrt(3)), (-3, -sqrt(3)), (-3, sqrt(3)), (0, 2*sqrt(3)), (3, sqrt(3)), (3, -sqrt(3))]
hexproto = QPolygonF([QPointF(*cs) for cs in vs])
pentproto = QPolygonF([QPointF(*cs) for cs in [(0, -sqrt(3))] + vs[2:]])

def distancesquared(v):
    return sum([vi * vi for vi in v])

def rotatedirection(direction, steps):
    return (direction + steps) % 6

def borders(grid, face, direction, edge):
    # edges are in CCW order: find edge of origin in list to orient
    count = 0
    for border in grid.borders(face, edge):
        yield (rotatedirection(direction, count + 1), border)
        count += 1

def dot(v1, v2):
    return sum([v1[i] * v2[i] for i in range(len(v1))])

radius = 5
radiussquared = radius * radius * distancesquared(offsets[0])

class HexGrid(object):
    def __init__(self, scene, grid, colors, face, orientation, (poilocation, poilabel)):
        faceitems = self._buildgrid(scene, grid, colors, face, *orientation)

        items = faceitems.values()
        items.append(self._addglyph(scene, u'@', faceitems[face]))

        edgelength = abs(acos(dot(*orientation[1])))
        ingrid, item = self._findpointofinterest(faceitems, poilocation, edgelength)
        if ingrid:
            items.append(self._addglyph(scene, poilabel, item))
            self.poidirection = None
        else:
            loc = item.boundingRect().center()
            self.poidirection = 90 + 180 * atan2(loc.y(), loc.x()) / pi

        self.group = scene.createItemGroup(items)

    def _shapecolors(self, colors, face):
        rgb = [s * 255 for s in colors[face]] if face in colors else 3 * [128]
        return (QPen(Qt.transparent), QColor(*rgb))

    def _addpoly(self, scene, colors, prototype, offset, face, rotation):
        item = scene.addPolygon(prototype.translated(*offset), *self._shapecolors(colors, face))
        item.setTransformOriginPoint(*offset)
        item.setRotation(rotation)
        return item

    def _populatevertex(self, grid, face, vertex):
        if len(grid.vertices[vertex]) < 3:
            for neighbor in grid.prev.vertices[face]:
                grid.populate(neighbor)

    @staticmethod
    def _addoffsets(o1, o2):
        return tuple([o1[i] + o2[i] for i in range(2)])

    def _findpointofinterest(self, faceitems, location, r):
        mindist = float('inf'), None
        for face, item in faceitems.iteritems():
            dist = abs(acos(dot(face, location)))
            if dist < mindist[0] or (dist == mindist[0] and face < mindist[1]):
                mindist = dist, face, item
        return mindist[0] < r, mindist[2]

    def _addhexes(self, scene, grid, colors, face, direction, edge):
        faceitems = {}
        # store pentagons for further processing
        pentfaces = set()

        # queue items are (face, direction traversed from, edge crossed, offset) tuples
        q = [(face, direction, edge, (0,0))]
        seen = set()
        while len(q) > 0:
            face, whence, edge, offset = q.pop()
            if face not in seen:
                # add tile to the scene
                seen.add(face)
                faceitems[face] = self._addpoly(scene, colors, hexproto, offset, face, 0)

                # for each other edge
                for nextdir, border in borders(grid, face, whence, edge):
                    # ensure the neighboring face is populated
                    for v in border:
                       self._populatevertex(grid, face, v)
                    nextoffset = self._addoffsets(offset, offsets[nextdir])
                    if distancesquared(nextoffset) < radiussquared:
                        # enqueue for processing
                        q.insert(0, (grid.neighbor(face, border), (nextdir + 3) % 6, border, nextoffset))
                if len(grid.faces[face]) == 5:
                    pentfaces.add((face, offset))

        return faceitems, pentfaces

    def _distortvertex(self, scene, offset, displacement, vertexindex, rotation):
        item = scene.itemAt(*self._addoffsets(offset, displacement))
        polygon = item.polygon()
        matrix = QMatrix()
        matrix.rotate(rotation)
        rotated = matrix.map(pentproto.value(0)).toTuple()
        polygon.replace(vertexindex, QPointF(*self._addoffsets(rotated, offset)))
        item.setPolygon(polygon)

    def _addpents(self, scene, colors, oldfaceitems, pents):
        faceitems = dict(oldfaceitems)
        for face, offset in pents:
            # replace hex tile with a pentagon
            item = scene.itemAt(*offset)
            scene.removeItem(item)

            # pentagons are drawn by replacing three sides of a hex with two
            # new sides: find which neighboring tiles are populated to orient
            # the new vertex in the most aesthetic way
            populated = []
            for ni in range(len(offsets)):
                if scene.itemAt(*self._addoffsets(offset, offsets[ni])) is not None:
                    if len(populated) > 0 and populated[-1] + 1 != ni:
                        ni -= 6
                    populated.append(ni)
            base = sorted(populated)[len(populated)/2] if len(populated) > 0 else 0

            rotation = -60 * (base + 3)
            faceitems[face] = self._addpoly(scene, colors, pentproto, offset, face, rotation)
            for counter in (0, 1):
                # look for neighbors two clockwise and two counter- from base
                steps = -2 + 4*counter
                ni = rotatedirection(base, steps)
                if ni in [n%6 for n in populated]:
                    self._distortvertex(
                        scene,
                        offset,
                        offsets[ni],
                        rotatedirection(3, -ni + counter),
                        rotation)
        return faceitems

    def _buildgrid(self, scene, grid, colors, face, direction, edge):
        faceitems, pents = self._addhexes(scene, grid, colors, face, direction, edge)
        return self._addpents(scene, colors, faceitems, pents)

    def _addglyph(self, scene, glyph, item):
        offset = item.boundingRect().center().toTuple()
        text = scene.addText(glyph)
        metrics = QFontMetrics(text.font())
        text.translate(offset[0] - metrics.width(glyph) * 0.2, offset[1] - metrics.height() * 0.2)
        text.scale(0.2, 0.2)
        return text
