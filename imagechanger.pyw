#coding=utf-8
#!/usr/bin/env python
# Copyright (c) 2007-8 Qtrac Ltd. All rights reserved.
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later version. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.

import os
import platform
import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import qrc_resources
import numpy,scipy
from scipy import misc
import glob
import pydicom
from scipy import misc
from canvas import Canvas
from shape import Shape
from utils import read_NIM_CT_data

__version__ = "1.0.0"


class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.canvas = Canvas()

        scrollArea = QScrollArea()
        scrollArea.setWidget(self.canvas)
        scrollArea.setWidgetResizable(True)
        self.scrollBars = {
            Qt.Vertical: scrollArea.verticalScrollBar(),
            Qt.Horizontal: scrollArea.horizontalScrollBar(),
        }
        self.setCentralWidget(self.canvas)

        # logDockWidget = QDockWidget("Log", self)
        # logDockWidget.setObjectName("LogDockWidget")
        # logDockWidget.setAllowedAreas(Qt.LeftDockWidgetArea |
        #                               Qt.RightDockWidgetArea)
        # self.listWidget = QListWidget()
        # self.listWidget.setFocusPolicy(Qt.NoFocus)
        # logDockWidget.setWidget(self.listWidget)
        # self.addDockWidget(Qt.RightDockWidgetArea, logDockWidget)

        self.sizeLabel = QLabel()
        self.sizeLabel.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        status = self.statusBar()
        status.setSizeGripEnabled(False)
        status.addPermanentWidget(self.sizeLabel)
        status.showMessage("Ready", 5000)

        adjustDockWidget = QDockWidget("adjust", self)
        adjustDockWidget.setObjectName("adjustDockWidget")
        adjustDockWidget.setAllowedAreas(Qt.LeftDockWidgetArea |
                                         Qt.RightDockWidgetArea)
        self.slidermin = QSlider()
        self.slidermin.setOrientation(Qt.Horizontal)
        self.slidermin.setFocusPolicy(Qt.NoFocus)
        self.slidermax = QSlider()
        self.slidermax.setOrientation(Qt.Horizontal)
        self.slidermax.setFocusPolicy(Qt.NoFocus)
        self.labelmin = QLabel()
        self.labelmin.setMinimumSize(20, 40)
        self.labelmax = QLabel()
        self.labelmax.setMinimumSize(20, 40)

        self.connect(self.slidermin, SIGNAL('valueChanged(int)'), self.genImage1)
        self.connect(self.slidermax, SIGNAL('valueChanged(int)'), self.genImage2)

        adjustLayout = QGridLayout()
        adjustLayout.addWidget(self.slidermin, 0, 0)
        adjustLayout.addWidget(self.labelmin, 0, 1)
        adjustLayout.addWidget(self.slidermax, 1, 0)
        adjustLayout.addWidget(self.labelmax, 1, 1)
        adjustWidget = QWidget()
        adjustWidget.setLayout(adjustLayout)
        adjustDockWidget.setWidget(adjustWidget)
        self.addDockWidget(Qt.RightDockWidgetArea, adjustDockWidget)

        fileOpenAction = self.createAction("&Open...", self.fileOpen,
                                           QKeySequence.Open, "fileopen",
                                           "Open an existing image file")
        labelOpenAction = self.createAction('read label', self.labelOpen)
        fileSaveAction = self.createAction("&Save", self.fileSave,
                                           QKeySequence.Save, "filesave", "Save the image")
        fileSaveAsAction = self.createAction("Save &As...",
                                             self.fileSaveAs, icon="filesaveas",
                                             tip="Save the image using a new name")
        fileQuitAction = self.createAction("&Quit", self.close,
                                           "Ctrl+Q", "filequit", "Close the application")

        editZoomAction = self.createAction("&Zoom...", self.editZoom,
                                           "Alt+Z", "editzoom", "Zoom the image")

        helpAboutAction = self.createAction("&About Image Changer",
                                            self.helpAbout)

        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenuActions = (fileOpenAction,labelOpenAction,
                                fileSaveAction, fileSaveAsAction, None,
                                fileQuitAction)
        self.connect(self.fileMenu, SIGNAL("aboutToShow()"),
                     self.updateFileMenu)
        editMenu = self.menuBar().addMenu("&Edit")
        self.addActions(editMenu, (editZoomAction,))
        helpMenu = self.menuBar().addMenu("&Help")
        self.addActions(helpMenu, (helpAboutAction, ))

        fileToolbar = self.addToolBar("File")
        fileToolbar.setObjectName("FileToolBar")
        self.addActions(fileToolbar, (fileOpenAction,
                                      fileSaveAsAction))
        editToolbar = self.addToolBar("Edit")
        editToolbar.setObjectName("EditToolBar")

        self.zoomSpinBox = QSpinBox()
        self.zoomSpinBox.setRange(1, 400)
        self.zoomSpinBox.setSuffix(" %")
        self.zoomSpinBox.setValue(100)
        self.zoomSpinBox.setSingleStep(5)
        self.zoomSpinBox.setToolTip("Zoom the image")
        self.zoomSpinBox.setStatusTip(self.zoomSpinBox.toolTip())
        self.zoomSpinBox.setFocusPolicy(Qt.NoFocus)
        self.connect(self.zoomSpinBox,
                     SIGNAL("valueChanged(int)"), self.update)
        editToolbar.addWidget(self.zoomSpinBox)


        self.modeComboBox = QComboBox()
        self.modeComboBox.addItems(['create polygon', 'edit polygon'])
        self.modeComboBox.setCurrentIndex(1)
        self.connect(self.modeComboBox, SIGNAL('currentIndexChanged(int)'), self.fun1)
        self.modeComboBox.setFocusPolicy(Qt.NoFocus)
        editToolbar.addWidget(self.modeComboBox)


        settings = QSettings()
        self.recentFiles = settings.value("RecentFiles").toStringList()
        size = settings.value("MainWindow/Size",
                              QVariant(QSize(600, 500))).toSize()
        self.resize(size)
        position = settings.value("MainWindow/Position",
                                  QVariant(QPoint(0, 0))).toPoint()
        self.move(position)
        # self.restoreState(
        #     settings.value("MainWindow/State").toByteArray())

        self.setWindowTitle("Image Changer")
        self.updateFileMenu()
        # QTimer.singleShot(0, self.loadInitialFile)




    def createAction(self, text, slot=None, shortcut=None, icon=None,
                     tip=None, checkable=False, signal="triggered()"):
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(":/%s.png" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            self.connect(action, SIGNAL(signal), slot)
        if checkable:
            action.setCheckable(True)
        return action

    def addActions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

    def closeEvent(self, event):
        if self.okToContinue():
            settings = QSettings()
            filename = QVariant(QString(self.canvas.filename)) \
                if self.canvas.filename is not None else QVariant()
            settings.setValue("LastFile", filename)
            recentFiles = QVariant(self.recentFiles) \
                if self.recentFiles else QVariant()
            settings.setValue("RecentFiles", recentFiles)
            settings.setValue("MainWindow/Size", QVariant(self.size()))
            settings.setValue("MainWindow/Position",
                              QVariant(self.pos()))
            # settings.setValue("MainWindow/State",
            #                   QVariant(self.saveState()))
        else:
            event.ignore()

    def okToContinue(self):
        if self.canvas.dirty:
            reply = QMessageBox.question(self,
                                         "Image Changer - Unsaved Changes",
                                         "Save unsaved changes?",
                                         QMessageBox.Yes | QMessageBox.No |
                                         QMessageBox.Cancel)
            if reply == QMessageBox.Cancel:
                return False
            elif reply == QMessageBox.Yes:
                self.fileSave()
        return True

    def loadInitialFile(self):
        settings = QSettings()
        fname = unicode(settings.value("LastFile").toString())
        if fname and QFile.exists(fname):
            self.loadFile(fname)

    def updateStatus(self, message):
        self.statusBar().showMessage(message, 5000)
        if self.canvas.filename is not None:
            self.setWindowTitle("Image Changer - %s[*]" % \
                                os.path.basename(self.canvas.filename))
        elif not self.image.isNull():
            self.setWindowTitle("Image Changer - Unnamed[*]")
        else:
            self.setWindowTitle("Image Changer[*]")
        self.setWindowModified(self.canvas.dirty)

    def updateFileMenu(self):
        self.fileMenu.clear()
        self.addActions(self.fileMenu, self.fileMenuActions[:-1])
        current = QString(self.canvas.filename) \
            if self.canvas.filename is not None else None
        recentFiles = []
        for fname in self.recentFiles:
            if fname != current and QFile.exists(fname):
                recentFiles.append(fname)
        if recentFiles:
            self.fileMenu.addSeparator()
            for i, fname in enumerate(recentFiles):
                action = QAction(QIcon(":/icon.png"), "&%d %s" % (
                    i + 1, QFileInfo(fname).fileName()), self)
                action.setData(QVariant(fname))
                self.connect(action, SIGNAL("triggered()"),
                             self.loadFile)
                self.fileMenu.addAction(action)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.fileMenuActions[-1])


    def fileOpen(self):
        if not self.okToContinue():
            return
        dir = os.path.dirname(self.canvas.filename) \
            if self.canvas.filename is not None else "."
        dirname = unicode(QFileDialog.getExistingDirectory(self,
                                                    "Image Changer - Choose Image directory", dir,
                                                    QFileDialog.ShowDirsOnly))
        if dirname:
            filenames = glob.glob(dirname+'\\*.bin')
            if filenames:
                self.canvas.filenames = filenames
                self.canvas.index = 0
                self.loadFile(self.canvas.filenames[self.canvas.index])
                return
            filenames = glob.glob(dirname + '\\*.dcm')
            if filenames:
                self.canvas.filenames = filenames
                self.canvas.index = 0
                self.loadFile(self.canvas.filenames[self.canvas.index])
                return
            self.statusBar().showMessage('empty directory', 5000)

    def loadFile(self, fname=None):
        if fname is None:
            action = self.sender()
            if isinstance(action, QAction):
                fname = unicode(action.data().toString())
                if not self.okToContinue():
                    return
            else:
                return
        if fname:
            self.canvas.filename = None
            if fname.endswith('.bin'):
                self.canvas.imagedata = read_NIM_CT_data(fname, False)
            if fname.endswith('.dcm'):
                self.canvas.imagedata = pydicom.dcmread(fname).pixel_array
            self.canvas.GrayTo0 = self.canvas.imagedata.min()
            self.canvas.GrayTo255 = self.canvas.imagedata.max()
            imagedata = misc.bytescale(self.canvas.imagedata)
            imgshape = imagedata.shape
            image = QImage(imagedata, imgshape[1], imgshape[0],imgshape[1], QImage.Format_Indexed8)
            image.setColorTable([QColor(i,i,i).rgb() for i in range(256)])
            if image.isNull():
                message = "Failed to read %s" % fname
            else:
                self.addRecentFile(fname)
                self.canvas.image = image
                self.canvas.filename = fname
                self.canvas.dirty = False
                self.sizeLabel.setText("%d x %d" % (
                    image.width(), image.height()))
                message = "Loaded %s" % os.path.basename(fname)
                self.slidermin.setRange(self.canvas.imagedata.min(), self.canvas.imagedata.max())
                self.slidermin.setValue(self.canvas.imagedata.min())
                self.labelmin.setText(str(self.canvas.imagedata.min()))
                self.slidermax.setRange(self.canvas.imagedata.min(), self.canvas.imagedata.max())
                self.slidermax.setValue(self.canvas.imagedata.max())
                self.labelmax.setText(str(self.canvas.imagedata.max()))
                self.canvas.shapes = []
                self.canvas.current = None
                self.canvas.update()
            self.updateStatus(message)

    def addRecentFile(self, fname):
        if fname is None:
            return
        if not self.recentFiles.contains(fname):
            self.recentFiles.prepend(QString(fname))
            while self.recentFiles.count() > 9:
                self.recentFiles.takeLast()

    def fileSave(self):
        if self.canvas.image.isNull():
            return
        if not self.canvas.shapes:
            return
        if self.canvas.filename is None:
            self.fileSaveAs()
        else:
            self.canvas.saveLabel()
            self.updateStatus("Saved as %s" % self.canvas.filename)
            self.canvas.dirty = False

    def fileSaveAs(self):
        if self.canvas.image.isNull():
            return
        fname = self.filename if self.filename is not None else "."
        formats = ["*.%s" % unicode(format).lower() \
                   for format in QImageWriter.supportedImageFormats()]
        fname = unicode(QFileDialog.getSaveFileName(self,
                                                    "Image Changer - Save Image", fname,
                                                    "Image files (%s)" % " ".join(formats)))
        if fname:
            if "." not in fname:
                fname += ".png"
            self.addRecentFile(fname)
            self.filename = fname
            self.fileSave()


    def editZoom(self):
        if self.canvas.image.isNull():
            return
        percent, ok = QInputDialog.getInteger(self,
                                              "Image Changer - Zoom", "Percent:",
                                              self.zoomSpinBox.value(), 1, 400)
        if ok:
            self.zoomSpinBox.setValue(percent)

    def showImage(self, percent=None):
        if self.image.isNull():
            return
        if percent is None:
            percent = self.zoomSpinBox.value()
        factor = percent / 100.0
        width = self.image.width() * factor
        height =self.image.height() * factor
        image = self.image.scaled(width, height, Qt.KeepAspectRatio)
        self.imageLabel.setPixmap(QPixmap.fromImage(image))
        self.update()

    def helpAbout(self):
        QMessageBox.about(self, "About Image Changer",
                          """<b>Image Changer</b> v %s
                          <p>Copyright &copy; 2007 Qtrac Ltd. 
                          All rights reserved.
                          <p>This application can be used to perform
                          simple image manipulations.
                          <p>Python %s - Qt %s - PyQt %s on %s""" % (
                              __version__, platform.python_version(),
                              QT_VERSION_STR, PYQT_VERSION_STR, platform.system()))




    def keyPressEvent(self, event):

        if event.key() == Qt.Key_Up and self.canvas.index>0:
            self.canvas.index -= 1
            self.loadFile(self.canvas.filenames[self.canvas.index])
        if event.key() == Qt.Key_Down and self.canvas.index<len(self.canvas.filenames)-1:
            self.canvas.index += 1
            self.loadFile(self.canvas.filenames[self.canvas.index])


    def record(self, y):
        self.origy = y

    def adjustGray(self, event):
        k = 1
        if event.buttons() == Qt.LeftButton:
            tempmin = self.GrayTo0 + k * (event.pos().y() - self.origy)
            tempmin = min(tempmin, self.GrayTo255)
            tempmin = max(tempmin, self.imagedata.min())
            imagedata = misc.bytescale(self.imagedata, cmin=tempmin, cmax=self.GrayTo255)
            self.labelmin.setText(str(tempmin))
        elif event.buttons() == Qt.RightButton:
            tempmax = self.GrayTo255 + k * (event.pos().y() - self.origy)
            tempmax = max(tempmax, self.GrayTo0)
            tempmax = min(tempmax, self.imagedata.max())
            imagedata = misc.bytescale(self.imagedata, cmin=self.GrayTo0, cmax=tempmax)
            self.labelmax.setText(str(tempmax))
        imgshape = imagedata.shape
        image = QImage(imagedata, imgshape[1], imgshape[0], imgshape[1], QImage.Format_Indexed8)
        image.setColorTable([QColor(i, i, i).rgb() for i in range(256)])
        self.image = image
        self.showImage()

    def saveGray(self, event):
        k=1
        if event.button() == Qt.LeftButton:
            tempmin = self.GrayTo0 + k * (event.pos().y() - self.origy)
            tempmin = min(tempmin, self.GrayTo255)
            tempmin = max(tempmin, self.imagedata.min())
            self.GrayTo0 = tempmin
            self.slidermin.setValue(tempmin)
        elif event.button() == Qt.RightButton:
            tempmax = self.GrayTo255 + k * (event.pos().y() - self.origy)
            tempmax = max(tempmax, self.GrayTo0)
            tempmax = min(tempmax, self.imagedata.max())
            self.GrayTo255 = tempmax
            self.slidermax.setValue(tempmax)

    def genImage1(self):
        if self.slidermin.value() < self.slidermax.value():
            imagedata = misc.bytescale(self.canvas.imagedata, cmin=self.slidermin.value(), cmax=self.slidermax.value())
            imgshape = imagedata.shape
            image = QImage(imagedata, imgshape[1], imgshape[0], imgshape[1], QImage.Format_Indexed8)
            image.setColorTable([QColor(i, i, i).rgb() for i in range(256)])
            self.canvas.image = image
            self.update()
            self.labelmin.setText(str(self.slidermin.value()))
            self.labelmax.setText(str(self.slidermax.value()))
            self.canvas.GrayTo0 = self.slidermin.value()
            self.canvas.GrayTo255 = self.slidermax.value()
        else:
            QMessageBox.about(self, u'警告',u'a必须小于b')
            self.slidermin.setValue(self.slidermax.value())


    def genImage2(self):
        if self.slidermin.value() < self.slidermax.value():
            imagedata = misc.bytescale(self.canvas.imagedata, cmin=self.slidermin.value(), cmax=self.slidermax.value())
            imgshape = imagedata.shape
            image = QImage(imagedata, imgshape[1], imgshape[0], imgshape[1], QImage.Format_Indexed8)
            image.setColorTable([QColor(i, i, i).rgb() for i in range(256)])
            self.canvas.image = image
            self.update()
            self.labelmin.setText(str(self.slidermin.value()))
            self.labelmax.setText(str(self.slidermax.value()))
            self.canvas.GrayTo0 = self.slidermin.value()
            self.canvas.GrayTo255 = self.slidermax.value()
        else:
            QMessageBox.about(self, u'警告', u'a必须小于b')
            self.slidermax.setValue(self.slidermin.value())


    def update(self, percent = None):
        if percent is not None:
            self.canvas.scale = percent/100.0
        self.canvas.update()


    def labelOpen(self):
        if not self.okToContinue():
            return
        dir = os.path.dirname(self.canvas.filename) \
            if self.canvas.filename is not None else "."
        fname = unicode(QFileDialog.getOpenFileName(self,
                                                    "Image Changer - Choose Image", dir,
                                                    "Image files (*.txt)"))
        if fname:
            self.loadLabel(fname)
            self.update()


    def loadLabel(self, fname):
        fname1 = '%s.dcm' %os.path.splitext(fname)[0]
        self.loadFile(fname1)
        with open(fname) as f:
            f.readline()
            temp = f.readline()
            shape = Shape()
            shape.close()
            while(temp):
                if not temp.startswith('roi'):
                    points = temp.split()
                    for point in points:
                        x, y = point.split(',')
                        shape.addPoint(QPoint(int(x),int(y)))
                else:
                    self.canvas.shapes.append(shape)
                    shape = Shape()
                    shape.close()
                temp = f.readline()
            self.canvas.shapes.append(shape)

    def fun1(self, index):
        if index == 0:
            self.canvas.mode = 'create'
        else:
            self.canvas.mode = 'edit'

def main():
    app = QApplication(sys.argv)
    app.setOrganizationName("Qtrac Ltd.")
    app.setOrganizationDomain("qtrac.eu")
    app.setApplicationName("Image Changer")
    app.setWindowIcon(QIcon(":/icon.png"))
    form = MainWindow()
    form.show()
    app.exec_()


main()

