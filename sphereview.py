#!/usr/bin/env python

"""PySide port of the opengl/hellogl example from Qt v4.x"""

import math
from OpenGL import GL
from PySide import QtCore, QtOpenGL

def squared_length(v):
    return sum([vi * vi for vi in v])

def length(v):
    return math.sqrt(squared_length(v))

def normal(v):
    d = 1.0 / length(v)
    return tuple([vi * d for vi in v])

class SphereView(QtOpenGL.QGLWidget):
    def __init__(self, grid, colors, rotationoffset, parent, index):
        QtOpenGL.QGLWidget.__init__(self, parent)

        self.grid = grid
        self.colors = colors
        self._rotationoffset = rotationoffset
        self.objects = []
        self.index = index
        self.xRot = 0
        self.yRot = self._rotationoffset * 16
        self.zRot = 0

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
        self.objects = [None for _ in range(self.grid.size + 1)]
        self.update()
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
        if GL.glCheckFramebufferStatus(GL.GL_FRAMEBUFFER) != GL.GL_FRAMEBUFFER_COMPLETE:
            return
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
            color = colors[t]
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

    def normalizeAngle(self, angle):
        while angle < 0:
            angle += 360 * 16
        while angle > 360 * 16:
            angle -= 360 * 16
        return angle
