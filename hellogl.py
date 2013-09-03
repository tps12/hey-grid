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

class GLWidget(QtOpenGL.QGLWidget):
	def __init__(self, grid, colors, rotationoffset, parent=None):
		QtOpenGL.QGLWidget.__init__(self, parent)

		self.grid = grid
		self.colors = colors
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
		self.update()
		self.index = -1
		GL.glShadeModel(GL.GL_SMOOTH)
		#GL.glEnable(GL.GL_DEPTH_TEST)
		GL.glEnable(GL.GL_CULL_FACE)
		GL.glEnable(GL.GL_LIGHTING)
		GL.glEnable(GL.GL_LIGHT0)
		GL.glEnable(GL.GL_LIGHT1)

	def update(self):
		grid = self.grid
		for i in range(len(self.objects) - 1, -1, -1):
			if self.objects[i] is not None:
				GL.glDeleteLists(self.objects[i], 1)
			self.objects[i] = self.makeGrid(grid, self.colors[i])
			grid = grid.prev

	def redraw(self):
		self.updateGL()

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

	def makeGrid(self, grid, colors):
		genList = GL.glGenLists(1)
		GL.glNewList(genList, GL.GL_COMPILE)

		for t, vs in grid.faces.iteritems():
			color = colors[t] if t in colors else (0.5, 0.5, 0.5)
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
