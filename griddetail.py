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

class GridDetail(QGraphicsScene):
    def __init__(self, grid, colors, face):
        QGraphicsScene.__init__(self)

        self.grid = grid
        self.colors = colors
        self.center(face)

    def center(self, face, orientation=None):
        grid = self.grid
        if face not in grid.faces:
            face = grid.faces.keys()[0]
        self._center = face

        for item in self.items():
            self.removeItem(item)

        # default to arbitrarily chosen local North edge
        direction = S if orientation is None else orientation[0]
        edge = tuple(sorted(grid.faces[face][0:2])) if orientation is None else orientation[1]

        self.offsetfaces = self.buildgrid(face, direction, edge)
        self._orientation = (direction, edge)

        self.addglyph(u'@')
        self.update()

    def shapecolors(self, face):
        rgb = [s * 255 for s in self.colors[face]] if face in self.colors else 3 * [128]
        return (QPen(Qt.transparent), QColor(*rgb))

    def addpoly(self, prototype, offset, face, rotation):
        item = self.addPolygon(prototype.translated(*offset), *self.shapecolors(face))
        item.setTransformOriginPoint(*offset)
        item.setRotation(rotation)

    @staticmethod
    def rotatedirection(direction, steps):
        return (direction + steps) % 6

    def borders(self, face, direction, edge):
        edges = self.edges(face)
        # edges are in CCW order: find edge of origin in list to orient
        source = edges.index(edge)
        count = 0
        for border in edges[source + 1:] + edges[:source]:
            yield (self.rotatedirection(direction, count + 1), border)
            count += 1

    def neighbor(self, face, border):
        # each edge has two common faces (if they exist in the grid)
        common = self.grid.vertices[border[0]] & self.grid.vertices[border[1]]
        if len(common) == 2:
            return list(common - { face })[0]

    def populatevertex(self, face, vertex):
        if len(self.grid.vertices[vertex]) < 3:
            for neighbor in self.grid.prev.vertices[face]:
                self.grid.populate(neighbor)

    @staticmethod
    def addoffsets(o1, o2):
        return tuple([o1[i] + o2[i] for i in range(2)])

    def addhexes(self, face, direction, edge):
        # record mapping of x,y offsets to face locations
        offsetfaces = {}
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
                self.addpoly(hexproto, offset, face, 0)

                # for each other edge
                for nextdir, border in self.borders(face, whence, edge):
                    # ensure the neighboring face is populated
                    for v in border:
                       self.populatevertex(face, v)
                    nextoffset = self.addoffsets(offset, offsets[nextdir])
                    if distancesquared(nextoffset) < radiussquared:
                        # enqueue for processing
                        q.insert(0, (self.neighbor(face, border), (nextdir + 3) % 6, border, nextoffset))
                offsetfaces[offset] = face
                if len(self.grid.faces[face]) == 5:
                    pentfaces.add((face, offset))

        return offsetfaces, pentfaces

    def distortvertex(self, offset, displacement, vertexindex, rotation):
        item = self.itemAt(*self.addoffsets(offset, displacement))
        polygon = item.polygon()
        matrix = QMatrix()
        matrix.rotate(rotation)
        rotated = matrix.map(pentproto.value(0)).toTuple()
        polygon.replace(vertexindex, QPointF(*self.addoffsets(rotated, offset)))
        item.setPolygon(polygon)

    def addpents(self, pents):
        for face, offset in pents:
            # replace hex tile with a pentagon
            self.removeItem(self.itemAt(*offset))

            # pentagons are drawn by replacing three sides of a hex with two
            # new sides: find which neighboring tiles are populated to orient
            # the new vertex in the most aesthetic way
            populated = []
            for ni in range(len(offsets)):
                if self.itemAt(*self.addoffsets(offset, offsets[ni])) is not None:
                    if len(populated) > 0 and populated[-1] + 1 != ni:
                        ni -= 6
                    populated.append(ni)
            base = sorted(populated)[len(populated)/2] if len(populated) > 0 else 0

            rotation = 60 * (base + 3)
            self.addpoly(pentproto, offset, face, rotation)
            for counter in (0, 1):
                # look for neighbors two clockwise and two counter- from base
                steps = -2 + 4*counter
                ni = self.rotatedirection(base, steps)
                if ni in [n%6 for n in populated]:
                    self.distortvertex(
                        offset,
                        offsets[ni],
                        self.rotatedirection(3, -ni + counter),
                        rotation)

    def buildgrid(self, face, direction, edge):
        grid = self.grid
        colors = self.colors
        offsetfaces, pents = self.addhexes(face, direction, edge)
        self.addpents(pents)
        return offsetfaces

    def addglyph(self, glyph):
        text = self.addText(glyph)
        metrics = QFontMetrics(text.font())
        text.translate(-2, sqrt(3)/2 + metrics.height() * 0.1)
        text.scale(0.2, -0.2)

    def edges(self, face):
        vertices = self.grid.faces[face]
        return [tuple(sorted(vs)) for vs in zip(vertices, vertices[1:] + vertices[0:1])]

    def move(self, direction):
        offset = offsets[dirs.index(direction)]
        try:
            face = self.offsetfaces[offset]
        except KeyError:
            return
        edge = list(set(self.edges(self._center)) & set(self.edges(face)))[0]
        self.center(face, ((dirs.index(direction) + 3) % 6, edge))

    def rotate(self, rotation):
        change = 1 if rotation == 'CW' else -1
        direction, edge = self._orientation
        self.center(self._center, (direction + change, edge))

    def legend(self, label, distance):
        text = self.addText(label)
        text.setDefaultTextColor(QColor(255, 255, 255))
        metrics = QFontMetrics(text.font())
        text.translate(-2 * 2 * radius - text.textWidth(), -sqrt(3)/2 * 2 * radius + metrics.height() * 0.1)
        text.scale(0.2, -0.2)
        self.addLine(-2 * 2 * radius - text.textWidth(), -sqrt(3)/2 * 2 * radius - metrics.height() * 0.1,
            -2 * 2 * radius - text.textWidth() + distance, -sqrt(3)/2 * 2 * radius - metrics.height() * 0.1, QPen(QColor(255, 255, 255)))
        self.update()
