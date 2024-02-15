import traceback, sys
from pathlib import Path
import time
import os
from PyQt6.QtWidgets import (QLabel, QPushButton, QSizePolicy,
                             QProgressBar, QVBoxLayout, QCheckBox,
                             QDateEdit, QHBoxLayout, QListWidget, QListWidgetItem, QAbstractItemView)
from PyQt6 import QtCore
from PyQt6.QtGui import *
from PyQt6.QtCore import pyqtSignal, QObject, pyqtSlot, QRunnable, QThreadPool, Qt
from wwc_AutoBookmarker import doQT, doChronoQT
from datetime import datetime
from hyperlinks import hyperlink_
import fitz
from utilities import openFile, showInFolder

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
        x = QSizePolicy()
        x.setHorizontalPolicy(QSizePolicy.Policy.Expanding)
        self.pbar.setSizePolicy(x)

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
        x.setHorizontalPolicy(QSizePolicy.Policy.Expanding)
        x.setVerticalPolicy(QSizePolicy.Policy.Expanding)
        self.setSizePolicy(x)
        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

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
        self.parent.vLayout.removeWidget(pbar)

    @pyqtSlot(object)
    def thread_error(self, obj):
        print('Thread error')

class dropLabelBkMk(dropLabel):
    def __init__(self,mainUI,parent):
        super().__init__(mainUI)
        self.parent=parent

    def dropEvent(self, event):
        # TODO: check the file is fully downloaded from Dropbox
        self.setAcceptDrops(False)
        fs = [Path(u.toLocalFile()) for u in event.mimeData().urls()]
        self.threadpool=QThreadPool()
        print(f'Max threads: {self.threadpool.maxThreadCount()}')
        for f in fs:
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
                self.parent.vLayout.addWidget(worker.pbar)
                self.threadpool.start(worker)
        self.setAcceptDrops(True)

class dropLabelChrono(dropLabel):
    def __init__(self,mainUI,parent=None):
        super().__init__(mainUI)
        self.parent=parent
    def dropEvent(self, event):
        fs = [u.toLocalFile().strip() for u in event.mimeData().urls()]
        folder=Path(fs[0]).resolve().parent
        self.mainUI.settings['Chronology']['files']=[str(Path(f).relative_to(folder)) for f in fs]
        self.mainUI.settings['Chronology']['abs_path']=str(Path(fs[0]).parent)
        self.mainUI.saveSettings()
        doChronoQT(*fs,remove_duplicates=self.parent.checkBox_removeDuplicates.isChecked(),
                   day=self.parent.checkBox_addDayOfWeek.isChecked(),
                   dob=datetime.combine(self.parent.dateEdit_DOB.date().toPyDate(),datetime.min.time()))

class dropLabelHyperlinks(dropLabel):
    def __init__(self,mainUI,parent=None):
        super().__init__(mainUI)
        self.parent=parent

class CdropLayoutBkMks(QVBoxLayout):
    def __init__(self,mainUI):
        super().__init__()
        self.mainUI = mainUI

        self.list=layoutList(self.mainUI,'Bookmarking')
        self.list.setAcceptableFiles(('.pdf',))
        self.button_bkmk=QPushButton('Make bookmarks')


        self.vLayout=QVBoxLayout()
        self.addWidget(self.button_bkmk)
        self.addLayout(self.vLayout)
        self.addLayout(self.list)

        self.list.list.dropped_files_signal.connect(self.saveSettingsFromList)
        self.button_bkmk.clicked.connect(self.bkmk)

        self.setSettings()


    def bkmk(self):
        fs = self.list.getFiles()
        self.threadpool=QThreadPool()
        print(f'Max threads: {self.threadpool.maxThreadCount()}')
        for f in fs:
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
                self.vLayout.addWidget(worker.pbar)
                self.threadpool.start(worker)
        pass

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
        self.vLayout.removeWidget(pbar)

    @pyqtSlot(tuple)
    def thread_error(self, tup):
        print('Thread error', tup)

    @pyqtSlot(object)
    def saveSettingsFromList(self, fs):
        self.mainUI.settings['Bookmarks']['files']=fs
        self.mainUI.saveSettings()

    def setSettings(self):
        if 'Bookmarks' in self.mainUI.settings:
            if 'files' in self.mainUI.settings['Bookmarks']:
                self.list.setList(self.mainUI.settings['Bookmarks']['files'])

class CdropLayoutHyperlinks(QVBoxLayout):
    def __init__(self, mainUI):
        super().__init__()
        self.mainUI=mainUI
        self.button_repeat=QPushButton('Hyperlink')
        self.layout_list_from_files=layoutList(self.mainUI,'From')
        self.layout_list_from_files.setAcceptableFiles(('.doc','.docx','.pdf'))
        self.layout_list_to_files=layoutList(self.mainUI, 'To')
        self.layout_list_to_files.setAcceptableFiles(('.pdf'))
        self.addWidget(self.button_repeat)
        vLayout=QHBoxLayout()
        vLayout.addLayout(self.layout_list_from_files)
        vLayout.addLayout(self.layout_list_to_files)
        self.addLayout(vLayout)
        self.button_repeat.clicked.connect(self.hyperlink)
        self.layout_list_to_files.list.dropped_files_signal.connect(self.saveSettingsToList)
        self.layout_list_from_files.list.dropped_files_signal.connect(self.saveSettingsFromList)
        self.setSettings()


    def hyperlink(self,event):
        self.from_files=self.layout_list_from_files.getFiles()
        self.to_files=self.layout_list_to_files.getFiles()
        hyperlink_(self.from_files,self.to_files)

    @pyqtSlot(object)
    def saveSettingsFromList(self, fs):
        self.mainUI.settings['Hyperlinks']['from_files']=fs
        self.mainUI.saveSettings()

    @pyqtSlot(object)
    def saveSettingsToList(self, fs):
        self.mainUI.settings['Hyperlinks']['to_files']=fs
        self.mainUI.saveSettings()
    def setSettings(self):
        if 'Hyperlinks' in self.mainUI.settings:
            if 'from_files' in self.mainUI.settings['Hyperlinks']:
                self.layout_list_from_files.list.setList(self.mainUI.settings['Hyperlinks']['from_files'])
            if 'to_files' in self.mainUI.settings['Hyperlinks']:
                self.layout_list_to_files.list.setList(self.mainUI.settings['Hyperlinks']['to_files'])


class CdropLayoutChronology(QVBoxLayout):
    def __init__(self,mainUI):
        super().__init__()
        self.mainUI=mainUI
        self.list=layoutList(self.mainUI,'Chrono files')
        self.list.setAcceptableFiles(('.pdf,'))
        self.button_chrono=QPushButton('Make chronology')
        self.checkBox_removeDuplicates=QCheckBox('Remove duplicates')
        self.checkBox_addDayOfWeek=QCheckBox('Add day of week')
        self.checkBox_addAge=QCheckBox('Add age')
        self.dateEdit_DOB=QDateEdit()

        self.addWidget(self.button_chrono)
        self.addWidget(self.checkBox_removeDuplicates)
        self.addWidget(self.checkBox_addDayOfWeek)
        hLayout=QHBoxLayout()
        hLayout.addWidget(self.checkBox_addAge)
        hLayout.addWidget(self.dateEdit_DOB)
        self.addLayout(hLayout)
        self.addLayout(self.list)

        self.button_chrono.clicked.connect(self.chrono)
        self.checkBox_removeDuplicates.stateChanged.connect(self.stateChangedRemoveDuplicates)
        self.checkBox_addDayOfWeek.stateChanged.connect(self.stateChangedAddDayOfWeek)
        self.checkBox_addAge.stateChanged.connect(self.stateChangedAddAge)
        self.dateEdit_DOB.dateChanged.connect(self.dateChanged)
        self.list.list.dropped_files_signal.connect(self.saveSettingsFromList)


        self.setSettings()

    def chrono(self,event):
        fs=self.list.getFiles()
        if fs:
            doChronoQT(*fs,remove_duplicates=self.checkBox_removeDuplicates.isChecked(),
                       day=self.checkBox_addDayOfWeek.isChecked(),
                       dob=datetime.combine(self.dateEdit_DOB.date().toPyDate(),datetime.min.time()))

    @pyqtSlot(object)
    def saveSettingsFromList(self, fs):
        self.mainUI.settings['Chronology']['files']=fs
        self.mainUI.saveSettings()

    def setSettings(self):
        if 'Chronology' in self.mainUI.settings:
            if 'removeDuplicates' in self.mainUI.settings['Chronology']:
                self.checkBox_removeDuplicates.setChecked(self.mainUI.settings['Chronology']['removeDuplicates'])
            if 'dayOfWeek' in self.mainUI.settings['Chronology']:
                self.checkBox_addDayOfWeek.setChecked(self.mainUI.settings['Chronology']['dayOfWeek'])
            if 'Age' in self.mainUI.settings['Chronology']:
                self.checkBox_addAge.setChecked(self.mainUI.settings['Chronology']['Age'])
            if 'DOB' in self.mainUI.settings['Chronology']:
                self.dateEdit_DOB.setDate(QtCore.QDate.fromString(self.mainUI.settings['Chronology']['DOB'],'dd-MM-yyyy'))
            if 'files' in self.mainUI.settings['Chronology']:
                self.list.setList(self.mainUI.settings['Chronology']['files'])

    def stateChangedRemoveDuplicates(self,state):
        self.mainUI.settings['Chronology']['removeDuplicates']=state
        self.mainUI.saveSettings()

    def stateChangedAddDayOfWeek(self,state):
        self.mainUI.settings['Chronology']['dayOfWeek']=state
        self.mainUI.saveSettings()

    def stateChangedAddAge(self,state):
        self.mainUI.settings['Chronology']['Age']=state
        self.mainUI.saveSettings()

    def dateChanged(self,date):
        self.mainUI.settings['Chronology']['DOB']=date.toString('dd-MM-yyyy')
        self.mainUI.saveSettings()

class list(QListWidget):
    dropped_files_signal = pyqtSignal(object)

    def __init__(self,mainUI=None):
        super().__init__(mainUI)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        self.mainUI=mainUI
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setAcceptableFiles(('.doc','.docx','.pdf')) #default acceptable files
        self.itemDoubleClicked.connect(self.dbl_click)
        self.actionDelete = QAction("Remove...", self)
        self.actionDelete.triggered.connect(self.deleteItem)
        self.addAction(self.actionDelete)
        self.actionFolder = QAction("Show folder...", self)
        self.actionFolder.triggered.connect(self.folderItem)
        self.addAction(self.actionFolder)


    def folderItem(self):
        item=Path(self.mainUI.settings['ReferenceFolder']) / self.currentItem().data(Qt.ItemDataRole.UserRole)
        showInFolder(item)

    def deleteItem(self):
        self.takeItem(self.currentRow())
        self.dropped_files_signal.emit(self.getRelFiles())

    def dbl_click(self,listWidgetItem):
        f=Path(self.mainUI.settings['ReferenceFolder']) / listWidgetItem.data(Qt.ItemDataRole.UserRole)
        openFile(f)
    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(QtCore.Qt.DropAction.CopyAction)
            event.accept()
        else:
            super(list, self).dragMoveEvent(event)
            #event.ignore()
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            super(list, self).dragEnterEvent(event)
            #event.ignore()

    def dropEvent(self, event):
        fs = [u.toLocalFile().strip() for u in event.mimeData().urls()]
        #rfs= [Path(f).relative_to(self.mainUI.settings['ReferenceFolder']) for f in fs]
        rfs=[os.path.relpath(f, os.path.dirname(self.mainUI.settings['ReferenceFolder'])) for f in fs]
        self.setList(rfs)
        super(list, self).dropEvent(event)
        self.dropped_files_signal.emit(self.getRelFiles())


    def setAcceptableFiles(self,tup):
        self.acceptable_files=tup
    def setList(self,fs):
        def itemExists(f):
            for i in range(self.count()):
                if self.item(i).data(Qt.ItemDataRole.UserRole) == f: return True
            return False
        for f in fs:
            if not itemExists(f) and Path(f).suffix.lower() in self.acceptable_files:
                item = QListWidgetItem(Path(f).stem + Path(f).suffix.lower())
                item.setData(Qt.ItemDataRole.UserRole, f)
                self.addItem(item)

    def getFiles(self):
        list=[]
        for i in range(self.count()):
            list.append(str(Path(self.mainUI.settings['ReferenceFolder']) / self.item(i).data(Qt.ItemDataRole.UserRole)))
        return list

    def getRelFiles(self):
        list=[]
        for i in range(self.count()):
            list.append(str(Path(self.item(i).data(Qt.ItemDataRole.UserRole))))
        return list


class layoutList(QVBoxLayout):
    def __init__(self,mainUI,name):
        super().__init__()
        self.mainUI=mainUI
        self.label=QLabel(name)
        self.list=list(self.mainUI)
        self.clear_button=QPushButton("Clear")
        self.addWidget(self.label)
        self.addWidget(self.list)
        self.addWidget(self.clear_button)
        self.clear_button.clicked.connect(self.clear)

    def setAcceptableFiles(self,tup):
        self.list.setAcceptableFiles(tup)

    def setList(self,fs):
        self.list.setList(fs)

    def getFiles(self):
        return self.list.getFiles()

    def getRelFiles(self):
        return self.list.getRelFiles()
    def clear(self):
        self.list.clear()
        self.list.dropped_files_signal.emit(self.list.getFiles())

