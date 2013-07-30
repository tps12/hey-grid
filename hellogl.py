#!/usr/bin/env python

"""PySide port of the opengl/hellogl example from Qt v4.x"""

from collections import deque
import sys
import math
from PySide import QtCore, QtGui, QtOpenGL

try:
	from OpenGL import GL
except ImportError:
	app = QtGui.QApplication(sys.argv)
	QtGui.QMessageBox.critical(None, "OpenGL hellogl",
							"PyOpenGL must be installed to run this example.",
							QtGui.QMessageBox.Ok | QtGui.QMessageBox.Default,
							QtGui.QMessageBox.NoButton)
	sys.exit(1)


class Window(QtGui.QWidget):
	def __init__(self, parent=None):
		QtGui.QWidget.__init__(self, parent)

		self.glWidget = GLWidget()

		self.xSlider = self.createSlider(QtCore.SIGNAL("xRotationChanged(int)"),
										 self.glWidget.setXRotation)
		self.ySlider = self.createSlider(QtCore.SIGNAL("yRotationChanged(int)"),
										 self.glWidget.setYRotation)
		self.zSlider = self.createSlider(QtCore.SIGNAL("zRotationChanged(int)"),
										 self.glWidget.setZRotation)

		mainLayout = QtGui.QHBoxLayout()
		mainLayout.addWidget(self.glWidget)
		mainLayout.addWidget(self.xSlider)
		mainLayout.addWidget(self.ySlider)
		mainLayout.addWidget(self.zSlider)
		self.setLayout(mainLayout)

		self.xSlider.setValue(15 * 16)
		self.ySlider.setValue(345 * 16)
		self.zSlider.setValue(0 * 16)

		self.setWindowTitle(self.tr("Hello GL"))

	def createSlider(self, changedSignal, setterSlot):
		slider = QtGui.QSlider(QtCore.Qt.Vertical)

		slider.setRange(0, 360 * 16)
		slider.setSingleStep(16)
		slider.setPageStep(15 * 16)
		slider.setTickInterval(15 * 16)
		slider.setTickPosition(QtGui.QSlider.TicksRight)

		self.glWidget.connect(slider, QtCore.SIGNAL("valueChanged(int)"), setterSlot)
		self.connect(self.glWidget, changedSignal, slider, QtCore.SLOT("setValue(int)"))

		return slider

class Tile(object):
	def __init__(self, id, edge_count):
		self.id = id
		self.edge_count = edge_count
		self.tiles = self.edge_count * [None]
		self.corners = self.edge_count * [None]
		self.edges = self.edge_count * [None]
                self.generation = None

class Corner(object):
	def __init__(self, id):
		self.id = id
		self.tiles = 3 * [None]
		self.corners = 3 * [None]
		self.edges = 3 * [None]

class Edge(object):
	def __init__(self, id):
		self.id = id
		self.tiles = 2 * [None]
		self.corners = 2 * [None]

class Grid(object):
	def __init__(self, size):
		self.size = size

		self.tiles = deque()
		for i in range(self.tile_count(self.size)):
			self.tiles.append(Tile(i, 5 if i<12 else 6))

		self.corners = deque()
		for i in range(self.corner_count(self.size)):
			self.corners.append(Corner(i))

		self.edges = deque()
		for i in range(self.edge_count(self.size)):
			self.edges.append(Edge(i))

	@staticmethod
	def tile_count(size):
		return 10*pow(3,size)+2

	@staticmethod
	def corner_count(size):
		return 20*pow(3,size)

	@staticmethod
	def edge_count(size):
		return 30*pow(3,size)

class GLWidget(QtOpenGL.QGLWidget):
	def __init__(self, parent=None):
		QtOpenGL.QGLWidget.__init__(self, parent)

		self.object = 0
		self.xRot = 0
		self.yRot = 0
		self.zRot = 0

		self.lastPos = QtCore.QPoint()

		self.trolltechGreen = QtGui.QColor.fromCmykF(0.40, 0.0, 1.0, 0.0)
		self.trolltechPurple = QtGui.QColor.fromCmykF(0.39, 0.39, 0.0, 0.0)

	def xRotation(self):
		return self.xRot

	def yRotation(self):
		return self.yRot

	def zRotation(self):
		return self.zRot

	def minimumSizeHint(self):
		return QtCore.QSize(50, 50)

	def sizeHint(self):
		return QtCore.QSize(400, 400)

	def setXRotation(self, angle):
		angle = self.normalizeAngle(angle)
		if angle != self.xRot:
			self.xRot = angle
			self.emit(QtCore.SIGNAL("xRotationChanged(int)"), angle)
			self.updateGL()

	def setYRotation(self, angle):
		angle = self.normalizeAngle(angle)
		if angle != self.yRot:
			self.yRot = angle
			self.emit(QtCore.SIGNAL("yRotationChanged(int)"), angle)
			self.updateGL()

	def setZRotation(self, angle):
		angle = self.normalizeAngle(angle)
		if angle != self.zRot:
			self.zRot = angle
			self.emit(QtCore.SIGNAL("zRotationChanged(int)"), angle)
			self.updateGL()

	def initializeGL(self):
		self.qglClearColor(self.trolltechPurple.darker())
		#self.object = self.makeObject()
		self.object = self.makeGrid()
		GL.glShadeModel(GL.GL_SMOOTH)
		#GL.glEnable(GL.GL_DEPTH_TEST)
		GL.glEnable(GL.GL_CULL_FACE)
		GL.glEnable(GL.GL_LIGHTING)
		GL.glEnable(GL.GL_LIGHT0)

	def paintGL(self):
		GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
		GL.glLoadIdentity()
		GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, (10, -10, -20, 0))
		GL.glTranslated(0.0, 0.0, -10.0)
		GL.glRotated(self.xRot / 16.0, 1.0, 0.0, 0.0)
		GL.glRotated(self.yRot / 16.0, 0.0, 1.0, 0.0)
		GL.glRotated(self.zRot / 16.0, 0.0, 0.0, 1.0)
		GL.glCallList(self.object)

	def resizeGL(self, width, height):
		side = min(width, height)
		GL.glViewport((width - side) / 2, (height - side) / 2, side, side)

		GL.glMatrixMode(GL.GL_PROJECTION)
		GL.glLoadIdentity()
		#GL.glOrtho(-0.5, +0.5, +0.5, -0.5, 4.0, 15.0)
		GL.glOrtho(-2, 2, 2, -1, 4.0, 15.0)
		GL.glMatrixMode(GL.GL_MODELVIEW)

	def mousePressEvent(self, event):
		self.lastPos = QtCore.QPoint(event.pos())

	def mouseMoveEvent(self, event):
		dx = event.x() - self.lastPos.x()
		dy = event.y() - self.lastPos.y()

		if event.buttons() & QtCore.Qt.LeftButton:
			self.setXRotation(self.xRot + 8 * dy)
			self.setYRotation(self.yRot - 8 * dx)
		elif event.buttons() & QtCore.Qt.RightButton:
			self.setXRotation(self.xRot + 8 * dy)
			self.setZRotation(self.zRot + 8 * dx)

		self.lastPos = QtCore.QPoint(event.pos())

	@classmethod
	def squared_length(cls, v):
		return sum([vi * vi for vi in v])

	@classmethod
	def length(cls, v):
		return math.sqrt(cls.squared_length(v))

	@classmethod
	def normal(cls, v):
		d = 1.0 / cls.length(v)
		return tuple([vi * d for vi in v])

	@classmethod
	def invert(cls, v):
		return tuple([-vi for vi in v])

	@classmethod
	def _add_corner(cls, id, grid, t1, t2, t3):
		c = grid.corners[id]
		t = [grid.tiles[i] for i in (t1, t2, t3)]

		v = tuple([sum([ti.v[i] for ti in t]) for i in range(3)])
		c.v = cls.normal(v)
		for i in range(3):
				t[i].corners[cls.position(t[i], t[(i+2)%3])] = c
				c.tiles[i] = t[i]

	@classmethod
	def _add_edge(cls, id, grid, t1, t2):
		e = grid.edges[id]
		t = [grid.tiles[i] for i in (t1, t2)]
		c = [
				grid.corners[t[0].corners[cls.position(t[0], t[1])].id],
				grid.corners[t[0].corners[(cls.position(t[0], t[1])+1)%t[0].edge_count].id]
			]
		for i in range(2):
				t[i].edges[cls.position(t[i], t[(i+1)%2])] = e
				e.tiles[i] = t[i]
				c[i].edges[cls.position(c[i], c[(i+1)%2])] = e
				e.corners[i] = c[i]
	
	@staticmethod
	def position(o, n):
		for os in (o.tiles, o.corners, o.edges):
			for i in range(len(os)):
				if os[i] == n:
					return i
		return -1

	def grid0(self):
		grid = Grid(0)

		x = -0.525731112119133606
		z = -0.850650808352039932
		
		icos_tiles = [
				(-x, 0, z), (x, 0, z), (-x, 0, -z), (x, 0, -z),
				(0, z, x), (0, z, -x), (0, -z, x), (0, -z, -x),
				(z, x, 0), (-z, x, 0), (z, -x, 0), (-z, -x, 0)
		]
		
		icos_tiles_n = [
				(9, 4, 1, 6, 11), (4, 8, 10, 6, 0), (11, 7, 3, 5, 9), (2, 7, 10, 8, 5),
				(9, 5, 8, 1, 0), (2, 3, 8, 4, 9), (0, 1, 10, 7, 11), (11, 6, 10, 3, 2),
				(5, 3, 10, 1, 4), (2, 5, 4, 0, 11), (3, 7, 6, 1, 8), (7, 2, 9, 0, 6)
		]
		
		for t in grid.tiles:
                                t.generation = 0
				t.v = icos_tiles[t.id]
				for k in range(5):
					t.tiles[k] = grid.tiles[icos_tiles_n[t.id][k]]
		for i in range(5):
				self._add_corner(i, grid, 0, icos_tiles_n[0][(i+4)%5], icos_tiles_n[0][i])
		for i in range(5):
				self._add_corner(i+5, grid, 3, icos_tiles_n[3][(i+4)%5], icos_tiles_n[3][i])
		self._add_corner(10,grid,10,1,8)
		self._add_corner(11,grid,1,10,6)
		self._add_corner(12,grid,6,10,7)
		self._add_corner(13,grid,6,7,11)
		self._add_corner(14,grid,11,7,2)
		self._add_corner(15,grid,11,2,9)
		self._add_corner(16,grid,9,2,5)
		self._add_corner(17,grid,9,5,4)
		self._add_corner(18,grid,4,5,8)
		self._add_corner(19,grid,4,8,1)
		
		#_add corners to corners
		for c in grid.corners:
				for k in range(3):
					c.corners[k] = c.tiles[k].corners[(self.position(c.tiles[k], c)+1)%5]
		#new edges
		next_edge_id = 0
		for t in grid.tiles:
				for k in range(5):
					if t.edges[k] is None:
						self._add_edge(next_edge_id, grid, t.id, icos_tiles_n[t.id][k])
						next_edge_id += 1
		return grid

	def _subgrid(self, prev):
		grid = Grid(prev.size + 1)

		prev_tile_count = len(prev.tiles)
		prev_corner_count = len(prev.corners)

		# old tiles
		for i in range(prev_tile_count):
			grid.tiles[i].v = prev.tiles[i].v
                        grid.tiles[i].generation = prev.tiles[i].generation
			for k in range(grid.tiles[i].edge_count):
				grid.tiles[i].tiles[k] = grid.tiles[prev.tiles[i].corners[k].id + prev_tile_count]

		# old corners become tiles
		for i in range(prev_corner_count):
			grid.tiles[i+prev_tile_count].v = prev.corners[i].v
			for k in range(3):
				grid.tiles[i+prev_tile_count].tiles[2*k] = grid.tiles[prev.corners[i].corners[k].id + prev_tile_count]
				grid.tiles[i+prev_tile_count].tiles[2*k+1] = grid.tiles[prev.corners[i].tiles[k].id]

		# new corners
		next_corner_id = 0
		for n in prev.tiles:
			t = grid.tiles[n.id]
			for k in range(t.edge_count):
				self._add_corner(next_corner_id, grid, t.id, t.tiles[(k+t.edge_count-1)%t.edge_count].id, t.tiles[k].id)
				next_corner_id += 1

		# connect corners
		for c in grid.corners:
			for k in range(3):
				c.corners[k] = c.tiles[k].corners[(self.position(c.tiles[k], c)+1)%c.tiles[k].edge_count]

		# new edges
		next_edge_id = 0
		for t in grid.tiles:
                        if t.generation is None:
                            t.generation = prev.tiles[-1].generation + 1
			for k in range(t.edge_count):
				if t.edges[k] is None:
					self._add_edge(next_edge_id, grid, t.id, t.tiles[k].id)
					next_edge_id += 1

		return grid

	# makes a spherical grid "subdivided" the given number of times
	#
	# a size 0 grid is a dodecahedron, and each subsequent size is the result
	# of taking the previous size and turning each vertex into a face
	#
	# therefore, the number of faces for a given sized grid is:
	#
	# >>> def f(i):
	# ...     return 12 if i == 0 else f(i-1) + v(f(i-1))
	#
	# where
	#
	# >>> def v(f):
	# ...     p = 12 # number of pentagons is fixed at 12
	# ...     h = f - p # everything else is a hexagon
	# ...     return p * 5/3 + h * 2
	#
	# a rectangular grid with approximate size of 2 degrees on a side provides
	# 10,316 tiles, a little more than the 7,292 provided by a size 6 hex grid
	# and well below the 21,872 provided by a size 7
	#
	# an earth-sized sphere divided into a grid of size 29
	# (686,303,773,648,832 tiles!) provides an average tile size of
	# 0.743 m^2 and around a linear meter between adjacent tiles
	def grid(self, size):
		return self.grid0() if size == 0 else self._subgrid(self.grid(size-1))

	def makeGrid(self):
		grid = self.grid(8)

		genList = GL.glGenLists(1)
		GL.glNewList(genList, GL.GL_COMPILE)

                cyan = (0, 1, 1, 1)
                gray = (0.5, 0.5, 0.5, 1)
                red = (1, 0, 0, 1)
		for t in grid.tiles:
                        color = red if t.generation == 0 else (gray if (t.generation % 2) == 0 else cyan)
                        GL.glMaterialfv(GL.GL_FRONT, GL.GL_DIFFUSE, color)
			GL.glBegin(GL.GL_TRIANGLE_FAN)
			n = self.normal(t.v)
			GL.glNormal3d(*n)
			GL.glVertex3d(*t.v)
			for c in t.corners:
				GL.glNormal3d(*n)
				GL.glVertex3d(*c.v)
			GL.glNormal3d(*n)
			GL.glVertex3d(*t.corners[0].v)
			GL.glEnd()

		GL.glEndList()

		return genList

	def makeObject(self):
		genList = GL.glGenLists(1)
		GL.glNewList(genList, GL.GL_COMPILE)

		GL.glBegin(GL.GL_QUADS)

		# "T" and tail of "Q"
		x1 = +0.06
		y1 = -0.14
		x2 = +0.14
		y2 = -0.06
		x3 = +0.08
		y3 = +0.00
		x4 = +0.30
		y4 = +0.22

		self.quad(x1, y1, x2, y2, y2, x2, y1, x1)
		self.quad(x3, y3, x4, y4, y4, x4, y3, x3)

		self.extrude(x1, y1, x2, y2)
		self.extrude(x2, y2, y2, x2)
		self.extrude(y2, x2, y1, x1)
		self.extrude(y1, x1, x1, y1)
		self.extrude(x3, y3, x4, y4)
		self.extrude(x4, y4, y4, x4)
		self.extrude(y4, x4, y3, x3)

		# circle of "Q", approximated in 200 sectors
		Pi = 3.14159265358979323846
		NumSectors = 200

		for i in range(NumSectors):
			angle1 = (i * 2 * Pi) / NumSectors
			x5 = 0.30 * math.sin(angle1)
			y5 = 0.30 * math.cos(angle1)
			x6 = 0.20 * math.sin(angle1)
			y6 = 0.20 * math.cos(angle1)

			angle2 = ((i + 1) * 2 * Pi) / NumSectors
			x7 = 0.20 * math.sin(angle2)
			y7 = 0.20 * math.cos(angle2)
			x8 = 0.30 * math.sin(angle2)
			y8 = 0.30 * math.cos(angle2)

			self.quad(x5, y5, x6, y6, x7, y7, x8, y8)

			self.extrude(x6, y6, x7, y7)
			self.extrude(x8, y8, x5, y5)

		GL.glEnd()
		GL.glEndList()

		return genList

	def quad(self, x1, y1, x2, y2, x3, y3, x4, y4):
		self.qglColor(self.trolltechGreen)

		GL.glVertex3d(x1, y1, -0.05)
		GL.glVertex3d(x2, y2, -0.05)
		GL.glVertex3d(x3, y3, -0.05)
		GL.glVertex3d(x4, y4, -0.05)

		GL.glVertex3d(x4, y4, +0.05)
		GL.glVertex3d(x3, y3, +0.05)
		GL.glVertex3d(x2, y2, +0.05)
		GL.glVertex3d(x1, y1, +0.05)

	def extrude(self, x1, y1, x2, y2):
		self.qglColor(self.trolltechGreen.darker(250 + int(100 * x1)))

		GL.glVertex3d(x1, y1, +0.05)
		GL.glVertex3d(x2, y2, +0.05)
		GL.glVertex3d(x2, y2, -0.05)
		GL.glVertex3d(x1, y1, -0.05)

	def normalizeAngle(self, angle):
		while angle < 0:
			angle += 360 * 16
		while angle > 360 * 16:
			angle -= 360 * 16
		return angle


if __name__ == '__main__':
	app = QtGui.QApplication(sys.argv)
	window = Window()
	window.show()
	sys.exit(app.exec_())
