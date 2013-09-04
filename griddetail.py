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

    def buildgrid(self, face, direction, edge):
        grid = self.grid
        colors = self.colors
        offsetfaces = {}
        # queue items are (face, direction traversed from, edge crossed, offset) tuples
        q = [(face, direction, edge, (0,0))]
        pents = []
        seen = set()
        while len(q) > 0:
            face, whence, edge, offset = q.pop()
            if face not in seen:
                seen.add(face)
                vertices = grid.faces[face]
                color = QColor(*[s * 255 for s in colors[face]]) if face in colors else QColor(128, 128, 128)
                self.addPolygon(hexproto.translated(*offset), QPen(Qt.transparent), color)
                offsetfaces[offset] = face
                if len(vertices) == 5:
                    pents.append((face, offset))
                edges = self.edges(face)
                # edges are in CCW order: find edge of origin in list to orient
                source = edges.index(edge)
                count = 0
                for border in edges[source + 1:] + edges[:source]:
                    for b in border:
                        if len(grid.vertices[b]) < 3:
                            for neighbor in grid.prev.vertices[face]:
                                grid.populate(neighbor)

                    commonfaces = list((grid.vertices[border[0]] & grid.vertices[border[1]]) - { face })
                    # one common face (if it exists in the grid)
                    if len(commonfaces) > 0:
                        nextdir = (whence + 1 + count) % 6
                        nextoffset = tuple([offset[i] + offsets[nextdir][i] for i in range(2)])
                        if distancesquared(nextoffset) < radiussquared:
                            q.insert(0, (commonfaces[0], (nextdir + 3) % 6, border, nextoffset))
                    count += 1
        for face, offset in pents:
            self.removeItem(self.itemAt(*offset))
            populated = []
            for ni in range(len(offsets)):
                if self.itemAt(*[offset[i] + offsets[ni][i] for i in range(2)]) is not None:
                    if len(populated) > 0 and populated[-1] + 1 != ni:
                        ni -= 6
                    populated.append(ni)
            base = sorted(populated)[len(populated)/2] if len(populated) > 0 else 0

            color = QColor(*[s * 255 for s in colors[face]]) if face in colors else QColor(128, 128, 128)
            item = self.addPolygon(pentproto.translated(*offset), QPen(Qt.transparent), color)
            offsetfaces[offset] = face
            item.setTransformOriginPoint(*offset)
            item.setRotation(60 * (base + 3))
            polygon = item.polygon()
            # look for neighbors two clockwise and two counter- from base
            for counter in (0, 1):
                ni = (base - 2 + 4 * counter) % 6
                if ni in [n%6 for n in populated]:
                    neighbor = self.itemAt(*[offset[i] + offsets[ni][i] for i in range(2)])
                    neighborpolygon = neighbor.polygon()
                    vertex = (3 - ni + counter) % 6
                    matrix = QMatrix()
                    matrix.rotate(item.rotation())
                    rotated = matrix.map(pentproto.value(0)).toTuple()
                    neighborpolygon.replace(vertex, QPointF(*[rotated[vi] + offset[vi] for vi in range(2)]))
                    neighbor.setPolygon(neighborpolygon)
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
