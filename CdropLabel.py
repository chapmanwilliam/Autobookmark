from PyQt6.QtWidgets import QLabel, QWidget, QPushButton, QSizePolicy
from PyQt6 import QtCore
from PyQt6.QtGui import *
from PyQt6.QtCore import pyqtSignal, QThread, QObject, pyqtSlot, QRunnable, QThreadPool
from wwc_AutoBookmarker import doQT
import fitz
from threading import Thread
import os


class Worker(QRunnable):
    progress_signal = pyqtSignal(int)

    def __init__(self, event):
        super().__init__()
        self.event = event

    def run(self):
        fs = [u.toLocalFile() for u in self.event.mimeData().urls()]
        for f in fs:
            f = f.replace('{', "").strip()
            print(f)
            if f != "":
                percentComplete = 0
                doQT(f, fitz.open(f), None, self.progress_signal)


class dropLabel(QLabel):
    def __init__(self, mainUI):
        super().__init__(mainUI)
        self.mainUI = mainUI
        self.setAcceptDrops(True)
        self.setText('DROP FILES HERE')
        x = QSizePolicy()
        x.setVerticalPolicy(QSizePolicy.Policy.Expanding)
        self.setSizePolicy(x)

        self.mainUI.progressBar.setRange(0, 100)
        self.mainUI.progressBar.setValue(0)

        f = self.font()
        f.setPointSize(20)  # sets the size to 50
        self.setFont(f)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        # TODO: check the file is fully downloaded from Dropbox
        worker = Worker(event)
        worker.progress_signal.connect(self.mainUI.progressBar.setValue)
        self.p_thread = QThreadPool()
        self.p_thread.start(worker)
        pass
