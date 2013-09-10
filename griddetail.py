from math import sqrt

from PySide.QtCore import QPointF, Qt
from PySide.QtGui import QColor, QFontMetrics, QGraphicsScene, QMatrix, QPen, QPolygonF

N, NW, SW, S, SE, NE = range(6)
dirs = ['N', 'NW', 'SW', 'S', 'SE', 'NE']
vs = [(-1, sqrt(3)), (1, sqrt(3)), (2, 0), (1, -sqrt(3)), (-1, -sqrt(3)), (-2, 0)]
offsets = [(0, 2*sqrt(3)), (-3, sqrt(3)), (-3, -sqrt(3)), (0, -2*sqrt(3)), (3, -sqrt(3)), (3, sqrt(3))]
hexproto = QPolygonF([QPointF(*cs) for cs in vs])
pentproto = QPolygonF([QPointF(*cs) for cs in [(0, sqrt(3))] + vs[2:]])

def distancesquared(v):
    return sum([vi * vi for vi in v])

radius = 5
radiussquared = radius * radius * distancesquared(offsets[0])

class HexGrid(object):
    def __init__(self, scene, grid, colors, face, orientation):
        self.grid = grid
        self.colors = colors

        items = self._buildgrid(scene, face, *orientation)

        items.append(self._addglyph(scene, u'@'))

        self.group = scene.createItemGroup(items)

    def _shapecolors(self, face):
        rgb = [s * 255 for s in self.colors[face]] if face in self.colors else 3 * [128]
        return (QPen(Qt.transparent), QColor(*rgb))

    def _addpoly(self, scene, prototype, offset, face, rotation):
        item = scene.addPolygon(prototype.translated(*offset), *self._shapecolors(face))
        item.setTransformOriginPoint(*offset)
        item.setRotation(rotation)
        return item

    def _borders(self, face, direction, edge):
        # edges are in CCW order: find edge of origin in list to orient
        count = 0
        for border in self.grid.borders(face, edge):
            yield (GridDetail._rotatedirection(direction, count + 1), border)
            count += 1

    def _populatevertex(self, face, vertex):
        if len(self.grid.vertices[vertex]) < 3:
            for neighbor in self.grid.prev.vertices[face]:
                self.grid.populate(neighbor)

    @staticmethod
    def _addoffsets(o1, o2):
        return tuple([o1[i] + o2[i] for i in range(2)])

    def _addhexes(self, scene, face, direction, edge):
        items = []
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
                items.append(self._addpoly(scene, hexproto, offset, face, 0))

                # for each other edge
                for nextdir, border in self._borders(face, whence, edge):
                    # ensure the neighboring face is populated
                    for v in border:
                       self._populatevertex(face, v)
                    nextoffset = self._addoffsets(offset, offsets[nextdir])
                    if distancesquared(nextoffset) < radiussquared:
                        # enqueue for processing
                        q.insert(0, (self.grid.neighbor(face, border), (nextdir + 3) % 6, border, nextoffset))
                if len(self.grid.faces[face]) == 5:
                    pentfaces.add((face, offset))

        return items, pentfaces

    def _distortvertex(self, scene, offset, displacement, vertexindex, rotation):
        item = scene.itemAt(*self._addoffsets(offset, displacement))
        polygon = item.polygon()
        matrix = QMatrix()
        matrix.rotate(rotation)
        rotated = matrix.map(pentproto.value(0)).toTuple()
        polygon.replace(vertexindex, QPointF(*self._addoffsets(rotated, offset)))
        item.setPolygon(polygon)

    def _addpents(self, scene, olditems, pents):
        items = list(olditems)
        for face, offset in pents:
            # replace hex tile with a pentagon
            item = scene.itemAt(*offset)
            scene.removeItem(item)
            items.remove(item)

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

            rotation = 60 * (base + 3)
            items.append(self._addpoly(scene, pentproto, offset, face, rotation))
            for counter in (0, 1):
                # look for neighbors two clockwise and two counter- from base
                steps = -2 + 4*counter
                ni = GridDetail._rotatedirection(base, steps)
                if ni in [n%6 for n in populated]:
                    self._distortvertex(
                        scene,
                        offset,
                        offsets[ni],
                        GridDetail._rotatedirection(3, -ni + counter),
                        rotation)
        return items

    def _buildgrid(self, scene, face, direction, edge):
        grid = self.grid
        colors = self.colors
        items, pents = self._addhexes(scene, face, direction, edge)
        return self._addpents(scene, items, pents)

    def _addglyph(self, scene, glyph):
        text = scene.addText(glyph)
        metrics = QFontMetrics(text.font())
        text.translate(-2, sqrt(3)/2 + metrics.height() * 0.1)
        text.scale(0.2, -0.2)
        return text

class GridDetail(object):
    def __init__(self, grid, colors, center, orientation=None):
        self.scene = QGraphicsScene()

        self.grid = grid
        self.colors = colors

        self._center = center

        # default to arbitrarily chosen local North edge
        self._orientation = (S, tuple(sorted(grid.faces[center][0:2]))) if orientation is None else orientation

        self._groups = [
            HexGrid(self.scene, self.grid, self.colors, self._center, self._orientation).group
        ]

    @staticmethod
    def _rotatedirection(direction, steps):
        return (direction + steps) % 6

    def _borders(self, face, direction, edge):
        # edges are in CCW order: find edge of origin in list to orient
        count = 0
        for border in self.grid.borders(face, edge):
            yield (self._rotatedirection(direction, count + 1), border)
            count += 1

    def move(self, direction):
        orientation = self._orientation
        for nextdir, border in self._borders(self._center, *orientation):
            if nextdir == dirs.index(direction):
                face = self.grid.neighbor(self._center, border)
                break
        else:
            face = self.grid.neighbor(self._center, orientation[1])
        edge = list(set(self.grid.edges(self._center)) & set(self.grid.edges(face)))[0]
        return GridDetail(self.grid, self.colors, face, ((dirs.index(direction) + 3) % 6, edge))

    def rotate(self, rotation):
        change = 1 if rotation == 'CW' else -1
        direction, edge = self._orientation
        return GridDetail(self.grid, self.colors, self._center, (direction + change, edge))
