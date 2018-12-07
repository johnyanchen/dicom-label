from PyQt4.QtCore import *
from PyQt4.QtGui import *
from shape import Shape
from utils import *
import os
class Canvas(QWidget):
    def __init__(self):
        super(Canvas, self).__init__()
        self.image = QImage()
        self.dirty = False
        self.filename = None
        self.filenames = []
        self.index = None
        self.scale = 1

        self.shapes = []
        self.current = None
        self.lineColor = QColor(0, 0, 255)
        self.line = Shape(self.lineColor)
        self.epsilon = 5
        self.setMouseTracking(True)

        self.mode = 'edit'
        self.selectShpae = None
        self.selectPoint = None
        self._mode = None

    def paintEvent(self, ev):
        if self.image is None:
            return
        p = QPainter()
        p.begin(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.HighQualityAntialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)

        p.scale(self.scale, self.scale)
        p.translate(self.offsetToCenter())

        p.drawImage(0, 0,self.image)

        for shape in self.shapes:
            shape.paint(p)
        if self.current:
            self.current.paint(p)
            self.line.paint(p)


        p.end()


    def mousePressEvent(self, ev):
        pos = self.transformPos(ev.pos())
        if self.mode == 'create':
            if self.current:
                self.current.addPoint(self.line[1])
                self.line[0] = self.line[1]
                if self.current.isClosed():
                    self.shapes.append(self.current)
                    self.current = None
                    self.line.line_color = self.lineColor
                    self.dirty = True
                    self.update()
            else:
                self.current = Shape()
                self.current.addPoint(pos)
                self.line.points = [pos, pos]
                self.update()
        elif self.mode == 'edit':
            for i, shape in enumerate(self.shapes):
                if isPosInPolygon(pos, shape):
                    shape.fill = True
                    self.preMovePos = pos
                    self.selectIndex = i
                    self.mode = 'drag'

    def mouseMoveEvent(self, ev):
        if self.mode == 'create':
            if not self.current:
                return
            pos = self.transformPos(ev.pos())
            color = self.lineColor
            if len(self.current)>1 and self.closeEnough(pos, self.current[0]):
                pos = self.current[0]
                color = self.current.line_color
                self.current._highlightIndex = 0
            self.line.line_color = color
            self.line[1] = pos
            self.repaint()
            self.current._highlightIndex = None
        elif self.mode == 'edit':
            pos = self.transformPos(ev.pos())
            for i, shape in enumerate(self.shapes):
                if isPosInPolygon(pos, shape):
                    shape.fill = True
                    self.repaint()
                    shape.fill = False
                    break
            else:
                self.repaint()
        elif self.mode == 'drag':
            pos = self.transformPos(ev.pos())
            self.shapes[self.selectIndex].moveTo(pos - self.preMovePos)
            self.preMovePos = pos
            self.repaint()

    def mouseReleaseEvent(self, ev):
        if self.mode == 'drag':
            self.mode = 'edit'



    def closeEnough(self, p1, p2):
        return distance(p1 - p2) < self.epsilon / self.scale

    def choosemode(self, pos):
        # for i,shape in enumerate(self.shapes):
        #     for j,point in enumerate(shape):
        #         if self.closeEnough(pos, point):
        #             self.selectShpae = i
        #             self.selectPoint = j
        #             self._mode = 'modify'
        #             return
        # for i, shape in enumerate(self.shapes):
        #     j = 0
        #     k = len(shape)-1
        #     while(j<len(shape)):
        #         if Pos2Lineseg(pos, shape[k], shape[j]) < self.epsilon / self.scale:
        #             self.selectShpae = i
        #             self.selectPoint = j
        #             self._mode = 'add'
        #             return
        #         k, j = j, j+1
        for i, shape in enumerate(self.shapes):
            if isPosInPolygon(pos, shape):
                self.selectShpae = i
                shape.fill = True
                self.repaint()
                shape.fill = False
                break
        else:
            self.selectShpae = None
            self.repaint()





    def offsetToCenter(self):
        s = self.scale
        area = super(Canvas, self).size()
        w, h = self.image.width() * s, self.image.height() * s
        aw, ah = area.width(), area.height()
        x = (aw - w) / (2 * s) if aw > w else 0
        y = (ah - h) / (2 * s) if ah > h else 0
        return QPoint(x, y)

    def transformPos(self, point):
        """Convert from widget-logical coordinates to painter-logical ones."""
        return point / self.scale - self.offsetToCenter()


    def saveLabel(self):
        labelName = '%s.txt' % os.path.splitext(self.filename)[0]
        with open(labelName, 'w') as f:
            for i, shape in enumerate(self.shapes):
                f.write('roi %d\n' %i)
                for j in range(len(shape)):
                    f.write('%d,%d ' %(shape[j].x(), shape[j].y()))
                f.write('\n')

