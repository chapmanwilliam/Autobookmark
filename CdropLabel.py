import traceback, sys
from pathlib import Path
import time

from PyQt6.QtWidgets import QLabel, QWidget, QPushButton, QSizePolicy,QProgressBar
from PyQt6 import QtCore
from PyQt6.QtGui import *
from PyQt6.QtCore import pyqtSignal, QThread, QObject, pyqtSlot, QRunnable, QThreadPool
from wwc_AutoBookmarker import doQT, doChronoQT
import fitz

class WorkerSignals(QObject):
    progress = pyqtSignal(int,object)
    error = pyqtSignal(tuple)
    result =pyqtSignal(str)
    finished = pyqtSignal(object)
    info = pyqtSignal(str,object)


class Worker(QRunnable):


    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args=args
        self.kwargs=kwargs
        self.signals=WorkerSignals()
        self.pbar=QProgressBar()
        self.pbar.setRange(0,100)
        self.pbar.setValue(0)
        self.pbar.setTextVisible(True)
        self.pbar.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        self.kwargs['progress_callback'] = self.signals.progress
        self.kwargs['info_callback'] = self.signals.info
        self.kwargs['progress_bar'] = self.pbar

    @pyqtSlot()
    def run(self):
        try:
            result=self.fn(*self.args,**self.kwargs)
        except:
            traceback.print_exc()
            exctype,value =sys.exc_info()[:2]
            self.signals.error.emit(exctype, value, traceback.format_exc())
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit(self.pbar)


class dropLabel(QLabel):
    def __init__(self, mainUI):
        super().__init__(mainUI)
        self.mainUI = mainUI
        self.setAcceptDrops(True)
        x = QSizePolicy()
        x.setVerticalPolicy(QSizePolicy.Policy.Expanding)
        self.setSizePolicy(x)

        f = self.font()
        f.setPointSize(20)  # sets the size to 50
        self.setFont(f)

        self.setStyleSheet("border: 1px solid black;")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()


    @pyqtSlot(int,object)
    def progress_fn(self, n,pbar):
        print(f"Percent {n}")
        pbar.setValue(n)

    @pyqtSlot(str)
    def print_out(self,s):
        print(s)

    @pyqtSlot(str,object)
    def info(self, s, pbar):
        print(s)
        pbar.setFormat(s)
    @pyqtSlot(object)
    def thread_complete(self,pbar):
        print('Thread completed')
        time.sleep(1)
        pbar.setFormat('')
        self.mainUI.verticalLayout.removeWidget(pbar)

    @pyqtSlot(object)
    def thread_error(self, obj):
        print('Thread error')

class CdropLabelBookmarks(dropLabel):
    def __init__(self,mainUI):
        super().__init__(mainUI)
        self.setText('Drop files for bookmarking')

    def dropEvent(self, event):
        # TODO: check the file is fully downloaded from Dropbox
        self.setAcceptDrops(False)
        fs = [u.toLocalFile() for u in event.mimeData().urls()]
        self.threadpool=QThreadPool()
        print(f'Max threads: {self.threadpool.maxThreadCount()}')
        for f in fs:
            f = f.replace('{', "").strip()
            print(f)
            if f != "":
                fl=fitz.open(f)
                worker=Worker(doQT,f=f,fl=fl)
                worker.signals.progress.connect(self.progress_fn)
                worker.signals.finished.connect(self.thread_complete)
                worker.signals.error.connect(self.thread_error)
                worker.signals.result.connect(self.print_out)
                worker.signals.info.connect(self.info)
                worker.pbar.setFormat(Path(f).stem)
                self.mainUI.verticalLayout.addWidget(worker.pbar)
                self.threadpool.start(worker)
        self.setAcceptDrops(True)

class CdropLabelChronology(dropLabel):
    def __init__(self,mainUI):
        super().__init__(mainUI)
        self.setText('Drop files for chronology')

    def dropEvent(self, event):
        fs = [u.toLocalFile().replace('{','').strip() for u in event.mimeData().urls()]
        doChronoQT(*fs)

            #Get bookmarks

            #For each bookmark
                # strip [] and legal numbering
                # is it a date?
                # extract date
                # extract description
                # extract page and page label
                # add to array of bookmarks

        #Sort the array of bookmarks in date order

        #Create pdf

        #Write the array of bookmarks to the pdf

        pass

    def getBookmarks(self,file_name):
        pass