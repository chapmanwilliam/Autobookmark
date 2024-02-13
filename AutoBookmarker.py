# -*- coding: utf-8 -*-
import sys
from pathlib import Path

from PyQt6.QtWidgets import QMainWindow, QApplication, QHBoxLayout, QFileDialog
from PyQt6.uic import loadUi
from PyQt6.QtCore import QThread, pyqtSignal
from CdropLabel import CdropLayoutBkMks, CdropLayoutChronology, CdropLayoutHyperlinks
import json

import wx

import frame_main





class MainUI(QMainWindow):
    def __init__(self):
        super(MainUI, self).__init__()
        loadUi('MainWindow.ui', self)
        self.getSettings()
        self.labelBookmark = CdropLayoutBkMks(self)
        self.labelChrono = CdropLayoutChronology(self)
        self.labelHyperlinks=CdropLayoutHyperlinks(self)
        self.horizontalLayout.addLayout(self.labelBookmark)
        self.horizontalLayout.addLayout(self.labelChrono)
        self.horizontalLayout.addLayout(self.labelHyperlinks)
        self.setWindowTitle('Autobookmark')
        self.actionSet_reference_folder.triggered.connect(self.setRefFolder)

    def setRefFolder(self):
        dlg=QFileDialog(self)
        dlg.setFileMode(QFileDialog.FileMode.Directory)
        if dlg.exec():
            dir=dlg.selectedFiles()[0]
            self.settings['ReferenceFolder']=dir + '/'
            self.saveSettings()
    def getSettings(self):
        try:
            f = open('settings.json')
            # returns JSON object as
            # a dictionary
            self.settings = json.load(f)
        except:
            print('No settings.json file')

    def saveSettings(self):
        with open('settings.json', 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, ensure_ascii=False, indent=4)



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
