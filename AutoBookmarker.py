# -*- coding: utf-8 -*-
import sys

from PyQt6.QtWidgets import QMainWindow, QApplication, QHBoxLayout
from PyQt6.uic import loadUi
from PyQt6.QtCore import QThread, pyqtSignal
from CdropLabel import dropLabel

import wx

import frame_main





class MainUI(QMainWindow):
    def __init__(self):
        super(MainUI, self).__init__()
        loadUi('MainWindow.ui', self)
        self.labelBookmark = dropLabel(self)
        self.labelChrono = dropLabel(self)
        self.horizontalLayout.addWidget(self.labelBookmark)
        self.horizontalLayout.addWidget(self.labelChrono)
        self.setWindowTitle('Autobookmark')




class AutoBookMarker(wx.App):
    def __init__(self):
        super(AutoBookMarker, self).__init__()
        self.frame = frame_main.FrameMain(None)
        self.SetTopWindow(self.frame)
        self.frame.Show()


#if __name__ == '__main__':
#    app = AutoBookMarker()
#    app.MainLoop()
#    sys.exit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = MainUI()
    ui.show()
    app.exec()
