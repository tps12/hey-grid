from math import sqrt

from PySide.QtCore import QPointF, Qt
from PySide.QtGui import QColor, QFontMetrics, QGraphicsScene, QMatrix, QPen, QPolygonF

N, NW, SW, S, SE, NE = range(6)
dirs = ['N', 'NW', 'SW', 'S', 'SE', 'NE']
vs = [(-1, sqrt(3)), (1, sqrt(3)), (2, 0), (1, -sqrt(3)), (-1, -sqrt(3)), (-2, 0)]
offsets = [(0, 2*sqrt(3)), (-3, sqrt(3)), (-3, -sqrt(3)), (0, -2*sqrt(3)), (3, -sqrt(3)), (3, sqrt(3))]
hexproto = QPolygonF([QPointF(*cs) for cs in vs])
pentproto = QPolygonF([QPointF(*cs) for cs in [(0, sqrt(3))] + vs[2:]])

class GridDetail(QGraphicsScene):
    def __init__(self, grids, colors, face):
        QGraphicsScene.__init__(self)

        self.grids = grids
        self.colors = colors
        self.face = face
        self.layer(len(self.grids) - 1)

    def layer(self, i, direction=None, edge=None):
        self._layer = i
        grid = self.grids[self._layer]
        colors = self.colors[self._layer]
        if self.face not in grid.faces:
            self.face = grid.faces.keys()[0]
        if len(grid.faces[self.face]) == 5:
            for f in grid.faces:
                if len(grid.faces[f]) == 6:
                    self.face = f
                    break
        face = self.face

        for item in self.items():
            self.removeItem(item)

        # initialize queue with face and arbitrarily chosen local North edge:
        # queue items are (face, direction traversed from, edge crossed, offset) tuples
        self.offsetfaces = {}
        direction = S if direction is None else direction
        edge = tuple(sorted(grid.faces[face][0:2])) if edge is None else edge
        q = [(face, direction, edge, (0,0))]
        pents = []
        seen = set()
        while len(q) > 0:
            face, whence, edge, offset = q.pop()
            if face not in seen:
                seen.add(face)
                vertices = grid.faces[face]
                if len(vertices) == 5:
                    pents.append((face, offset))
                    continue
                color = QColor(*[s * 255 for s in colors[face]])
                self.addPolygon(hexproto.translated(*offset), QPen(Qt.transparent), color)
                self.offsetfaces[offset] = face
                edges = self.edges(face)
                # edges are in CCW order: find edge of origin in list to orient
                source = edges.index(edge)
                count = 0
                for border in edges[source + 1:] + edges[:source]:
                    commonfaces = list((grid.vertices[border[0]] & grid.vertices[border[1]]) - { face })
                    # one common face (if it exists in the grid)
                    if len(commonfaces) > 0:
                        nextdir = (whence + 1 + count) % 6
                        nextoffset = tuple([offset[i] + offsets[nextdir][i] for i in range(2)])
                        q.insert(0, (commonfaces[0], (nextdir + 3) % 6, border, nextoffset))
                    count += 1
        for face, offset in pents:
            populated = []
            for ni in range(len(offsets)):
                if self.itemAt(*[offset[i] + offsets[ni][i] for i in range(2)]) is not None:
                    if len(populated) > 0 and populated[-1] + 1 != ni:
                        ni -= 6
                    populated.append(ni)
            base = sorted(populated)[len(populated)/2] if len(populated) > 0 else 0

            color = QColor(*[s * 255 for s in colors[face]])
            item = self.addPolygon(pentproto.translated(*offset), QPen(Qt.transparent), color)
            self.offsetfaces[offset] = face
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
        text = self.addText(u'@')
        metrics = QFontMetrics(text.font())
        text.translate(-2, sqrt(3)/2 + metrics.height() * 0.1)
        text.scale(0.2, -0.2)
        self.update()

    def edges(self, face):
        vertices = self.grids[self._layer].faces[face]
        return [tuple(sorted(vs)) for vs in zip(vertices, vertices[1:] + vertices[0:1])]

    def move(self, direction):
        face = self.offsetfaces[offsets[dirs.index(direction)]]
        edge = list(set(self.edges(self.face)) & set(self.edges(face)))[0]
        self.face = face
        self.layer(self._layer, (dirs.index(direction) + 3) % 6, edge)
