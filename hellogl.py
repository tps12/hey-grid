#!/usr/bin/env python

"""PySide port of the opengl/hellogl example from Qt v4.x"""

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

def squared_length(v):
	return sum([vi * vi for vi in v])

def length(v):
	return math.sqrt(squared_length(v))

def normal(v):
	d = 1.0 / length(v)
	return tuple([vi * d for vi in v])

def cross(v1, v2):
	return (
		v1[1]*v2[2] - v1[2]*v2[1],
		v1[2]*v2[0] - v1[0]*v2[2],
		v1[0]*v2[1] - v1[1]*v2[0])

def dot(v1, v2):
	return sum([v1[i] * v2[i] for i in range(3)])

def addface(fs, vs, f):
	for v in fs[f]:
		if v not in vs:
			vs[v] = vfs = set()
		else:
			vfs = vs[v]
		if f not in vfs:
			vfs.add(f)

def makeface(fs, vs, v, ns):
	nvs = []
	for n1, n2 in zip(ns, [ns[-1]] + ns):
		nvs.append(normal([sum([vi[i] for vi in sorted((v, n1, n2))]) for i in range(3)]))
	fs[v] = nvs
	addface(fs, vs, v)

class Grid(object):
	def __init__(self, prev=None):
		self.prev = prev
		self.size = self.prev.size + 1 if self.prev is not None else 0
		self.faces = {}
		self.vertices = {}

		if self.prev is None:
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

			for i in range(len(icos_tiles)):
				makeface(self.faces, self.vertices, icos_tiles[i], [icos_tiles[n] for n in icos_tiles_n[i]])

	# Populates grid by subdividing a single tile from the previous size
	#
	# If face is omitted, full previous size is subdivided
	def populate(self, f=None):
		grid = self
		prev = self.prev
		faces, vertices = self.faces, self.vertices

		if f is None:
			for f in prev.faces:
				self.populate(f)
			return

		if f in faces:
			return

		for v in prev.faces[f]:
			if len(prev.vertices[v]) < 3:
				# implies p was new in prev
				# i.e., p was a vertex in prev's prev
				# implies p in prev prev had three faces
				for n in prev.prev.vertices[f]:
					prev.populate(n)

		# face from face
		makeface(faces, vertices, f, prev.faces[f])

		# faces from vertices
		for v in prev.faces[f]:
			fs = prev.vertices[v]
			nvs = []
			lfs = list(fs)
			# for each pair of faces meeting at the previous vertex
			for f1, f2 in zip(lfs, lfs[1:] + lfs[0:1]):
				svs = list(set(prev.faces[f1]) & set(prev.faces[f2]))
				# new vertex at the midpoint between the two common old vertices and old face location
				for f in f1, f2:
					nvs.append(normal([sum([vi[i] for vi in sorted([f] + svs)]) for i in range(3)]))
			# make sure new vertices wind correctly
			faces[v] = nvs if dot(v, cross(*nvs[0:2])) > 0 else list(reversed(nvs))
			addface(faces, vertices, v)

	##
	# Notes
	#
	# Each face has 5 or 6 sides, and has
	#   - a unique index,
	#   - a location (a 1-length vector representing its center), and
	#   - a list of references to adjacent faces
	#
	# The unique index of a face at one resolution stays constant for the face
	# in the same location in subsequent resolutions: the face is smaller, and
	# gets new neighbors at higher resolutions, but otherwise stays put.
	#
	# A vertex at a given resolution
	#   - is uniquely identified by the three faces it touches and
	#   - is located at the mean of those faces' locations
	#
	# A face at a given resolution was either
	#   - a face of the previous resolution
	#       in which case
	#         . it's at the same location as previously and
	#         . each of its vertices is the midpoint of the face itself and the
	#             preceding face's two nearest vertices
	#       and therefore
	#         . can be entirely defined by the face's location and vertices
	#             at the preceding resolution
	#       or
	#   - a vertex of the previous resolution
	#       in which case
	#         . each of its vertices is the midpoint of two previous vertices
	#             and one previous face
	#       and therefore
	#         . can be entirely defined by the locations and vertices of the
	#             faces sharing the vertex at the preceding resolution
	# implying that, for a given resolution to be subdivided,
	#   - each face must be capable of being mapped to its vertices, and
	#   - each vertex must be mappable to the faces that share it

	@classmethod
	def _subgrid(self, prev):
		grid = self(prev)
		grid.populate()
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
	@classmethod
	def grid(self, size):
		return self() if size == 0 else self._subgrid(self.grid(size-1))

class GLWidget(QtOpenGL.QGLWidget):
	def __init__(self, grid, rotationoffset, parent=None):
		QtOpenGL.QGLWidget.__init__(self, parent)

		self.grid = grid
		self._rotationoffset = rotationoffset
		self.objects = []
		self.xRot = 0
		self.yRot = self._rotationoffset * 16
		self.zRot = 0

		self.lastPos = QtCore.QPoint()

		self.trolltechGreen = QtGui.QColor.fromCmykF(0.40, 0.0, 1.0, 0.0)
		self.trolltechPurple = QtGui.QColor.fromCmykF(0.39, 0.39, 0.0, 0.0)

	def minimumSizeHint(self):
		return QtCore.QSize(50, 50)

	def sizeHint(self):
		return QtCore.QSize(400, 400)

	def layer(self, index):
		if self.objects[index] != self.objects[self.index]:
			self.index = index
			self.updateGL()

	def rotate(self, angle):
		angle = self.normalizeAngle((angle + self._rotationoffset) * 16)
		if angle != self.yRot:
			self.yRot = angle
			self.updateGL()

	def initializeGL(self):
		self.qglClearColor(self.trolltechPurple.darker())
		self.objects = [None for _ in range(self.grid.size + 1)]
		grid = self.grid
		for i in range(len(self.objects) - 1, -1, -1):
			self.objects[i] = self.makeGrid(grid)
			grid = grid.prev
		self.index = -1
		GL.glShadeModel(GL.GL_SMOOTH)
		#GL.glEnable(GL.GL_DEPTH_TEST)
		GL.glEnable(GL.GL_CULL_FACE)
		GL.glEnable(GL.GL_LIGHTING)
		GL.glEnable(GL.GL_LIGHT0)
		GL.glEnable(GL.GL_LIGHT1)

	def paintGL(self):
		GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
		GL.glLoadIdentity()
		GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, (20, -10, -20, 0))
		GL.glLightfv(GL.GL_LIGHT1, GL.GL_DIFFUSE, (0.25, 0.25, 0.25, 1))
		GL.glLightfv(GL.GL_LIGHT1, GL.GL_POSITION, (-10, -5, -20, 0))
		GL.glTranslated(0.0, 0.0, -10.0)
		GL.glRotated(self.xRot / 16.0, 1.0, 0.0, 0.0)
		GL.glRotated(self.yRot / 16.0, 0.0, 1.0, 0.0)
		GL.glRotated(self.zRot / 16.0, 0.0, 0.0, 1.0)
		GL.glCallList(self.objects[self.index])

	def resizeGL(self, width, height):
		side = min(width, height)
		GL.glViewport((width - side) / 2, (height - side) / 2, side, side)

		GL.glMatrixMode(GL.GL_PROJECTION)
		GL.glLoadIdentity()
		GL.glOrtho(-1.1, 1.1, 1.1, -1.1, 0, 11)
		GL.glMatrixMode(GL.GL_MODELVIEW)

	def makeGrid(self, grid):
		genList = GL.glGenLists(1)
		GL.glNewList(genList, GL.GL_COMPILE)

                cyan = (0, 1, 1, 1)
                green = (0, 1, 0, 1)
                gray = (0.5, 0.5, 0.5, 1)
                red = (1, 0, 0, 1)
		for t, vs in grid.faces.iteritems():
                        color = red
                        color = green if t == grid.faces.keys()[4] else color
                        GL.glMaterialfv(GL.GL_FRONT, GL.GL_DIFFUSE, color)
			GL.glBegin(GL.GL_TRIANGLE_FAN)
			n = normal(t)
			GL.glNormal3d(*n)
			GL.glVertex3d(*t)
			for c in vs + [vs[0]]:
				GL.glVertex3d(*c)
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
