from PyQt4.QtCore import *
from PyQt4.QtGui import *

DEFAULT_LINE_COLOR = QColor(0, 255, 0, 128)
DEFAULT_VERTEX_FILL_COLOR = QColor(0, 255, 0, 255)
DEFAULT_HVERTEX_FILL_COLOR = QColor(255, 0, 0)
DEFAULT_FILL_COLOR = QColor(255, 0, 0, 128)
point_size = 4

class Shape(object):
    def __init__(self, line_color = DEFAULT_LINE_COLOR):
        self.points = []
        self._closed = False
        self._highlightIndex = None
        self.fill = False
        self.line_color = line_color

    def addPoint(self, point):
        if self.points and point == self.points[0]:
            self.close()
        else:
            self.points.append(point)

    def close(self):
        self._closed = True

    def isClosed(self):
        return self._closed

    def addPoint(self, point):
        if self.points and point == self.points[0]:
            self.close()
        else:
            self.points.append(point)

    def paint(self, painter):
        if self.points:
            color = self.line_color
            pen = QPen(color)
            pen.setWidth(2)
            painter.setPen(pen)

        line_path = QPainterPath()
        vrtx_path = QPainterPath()

        line_path.moveTo(self.points[0])
        for i, p in enumerate(self.points):
            line_path.lineTo(p)
            self.drawVertex(vrtx_path, i)
        if self.isClosed():
            line_path.lineTo(self.points[0])

        painter.drawPath(line_path)
        painter.drawPath(vrtx_path)
        if self._highlightIndex is not None:
            color = DEFAULT_HVERTEX_FILL_COLOR
        else:
            color = DEFAULT_VERTEX_FILL_COLOR
        painter.fillPath(vrtx_path, color)
        if self.fill:
            painter.fillPath(line_path, DEFAULT_FILL_COLOR)

    def drawVertex(self, path, i):
        d = point_size
        point = self.points[i]
        if i == self._highlightIndex:
            d *= 3
        path.addEllipse(point, d / 2.0, d / 2.0)


    def moveTo(self, pos):
        for shape in self.points:
            shape += pos

    def __len__(self):
        return len(self.points)

    def __getitem__(self, key):
        return self.points[key]

    def __setitem__(self, key, value):
        self.points[key] = value




