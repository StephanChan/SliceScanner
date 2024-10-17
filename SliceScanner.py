# -*- coding: utf-8 -*-
"""
Created on Wed Oct 16 11:09:15 2024

@author: admin
"""
import sys, os
import numpy as np
from queue import Queue
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QApplication
from PyQt5 import QtWidgets as QW
import PyQt5.QtCore as qc
from Generaic_functions import LOG
from Actions import *
from MainWindow import MainWindow

CQueue = Queue(maxsize = 0)
CBackQueue = Queue(maxsize = 0)
DOQueue = Queue(maxsize = 0)
StagebackQueue = Queue(maxsize = 0)
WeaverQueue = Queue(maxsize = 0)
PauseQueue = Queue(maxsize = 0)

from Camera import Camera
class Camera_2(Camera):
    def __init__(self, ui, log):
        super().__init__()
        self.ui = ui
        self.log = log
        self.queue = CQueue
        self.CBackQueue = CBackQueue
        
from ThreadDO_150mm import DOThread
class DOThread_2(DOThread):
    def __init__(self, ui, log):
        super().__init__()
        self.ui = ui
        self.queue = DOQueue
        self.StagebackQueue = StagebackQueue
        self.log = log
        self.SIM = False
        
from ThreadWeaver import WeaverThread
class WeaverThread_2(WeaverThread):
    def __init__(self, ui, log):
        super().__init__()
        self.ui = ui
        self.log = log
        self.queue = WeaverQueue
        self.CQueue = CQueue
        self.DOQueue = DOQueue
        self.PauseQueue = PauseQueue
        self.StagebackQueue = StagebackQueue
        self.CBackQueue = CBackQueue
        
class GUI(MainWindow):
    def __init__(self):
        super().__init__()
        self.log = LOG(self.ui)
        
        self.ui.SnapButton.clicked.connect(self.Snap)
        self.ui.Exposure.valueChanged.connect(self.SetExposure)
        self.ui.LiveButton.clicked.connect(self.Live)
        self.ui.AutoExpo.stateChanged.connect(self.AutoExposure)
        self.ui.MosaicButton.clicked.connect(self.Mosaic)
        self.ui.PauseButton.clicked.connect(self.Pause_task)
        
        self.ui.Xmove2.clicked.connect(self.Xmove2)
        self.ui.Ymove2.clicked.connect(self.Ymove2)
        # self.ui.Zmove2.clicked.connect(self.Zmove2)
        self.ui.XUP.clicked.connect(self.XUP)
        self.ui.YUP.clicked.connect(self.YUP)
        # self.ui.ZUP.clicked.connect(self.ZUP)
        self.ui.XDOWN.clicked.connect(self.XDOWN)
        self.ui.YDOWN.clicked.connect(self.YDOWN)
        # self.ui.ZDOWN.clicked.connect(self.ZDOWN)
        self.ui.UpdateButton.clicked.connect(self.InitStages)
        self.ui.UninitButton.clicked.connect(self.Uninit)
        
        self.weaver_thread = WeaverThread_2(self.ui, self.log)
        self.weaver_thread.start()
        self.DO_thread = DOThread_2(self.ui, self.log)
        self.DO_thread.start()
        self.Camera_thread = Camera_2(self.ui, self.log)
        self.Camera_thread.start()
        
    def Stop_allThreads(self):
        exit_element=EXIT()

        CQueue.put(exit_element) 
        DOQueue.put(exit_element) 
        
    def Snap(self):
        an_action = CAction('Snap')
        CQueue.put(an_action)
        # CBackQueue.get()

    def Live(self):
        an_action = CAction('Live')
        CQueue.put(an_action)
        
    def Mosaic(self):
        while PauseQueue.qsize()>0:
            PauseQueue.get()
        if self.ui.MosaicButton.isChecked():
            self.ui.MosaicButton.setText('Stop')
            # for surfScan and SurfSlice, popup a dialog to double check stage position
            an_action = WeaverAction('Mosaic')
            WeaverQueue.put(an_action)
        else:
            self.ui.MosaicButton.setText('Mosaic')
            self.Stop_task()
        
    def Pause_task(self):
        if self.ui.PauseButton.isChecked():
            PauseQueue.put('Pause')
            self.ui.PauseButton.setText('Resume')
            self.ui.statusbar.showMessage('acquisition paused...')
        else:
            PauseQueue.put('Resume')
            self.ui.PauseButton.setText('Pause')
            self.ui.statusbar.showMessage('acquisition resumed...')
      
    def Stop_task(self):
        PauseQueue.put('Stop')
        self.ui.statusbar.showMessage('acquisition stopped...')
        
    def SetExposure(self):
        an_action = CAction('SetExposure')
        CQueue.put(an_action)
        
    def AutoExposure(self):
        an_action = CAction('AutoExposure')
        CQueue.put(an_action)
        
    def InitStages(self):
        an_action = DOAction('Init')
        DOQueue.put(an_action)
        StagebackQueue.get()
        
    def Uninit(self):
        an_action = DOAction('Uninit')
        DOQueue.put(an_action)
        StagebackQueue.get()
        
    def Xmove2(self):
        an_action = DOAction('Xmove2')
        DOQueue.put(an_action)
        StagebackQueue.get()
        
    def Ymove2(self):
        an_action = DOAction('Ymove2')
        DOQueue.put(an_action)
        StagebackQueue.get()
        
    def Zmove2(self):
        an_action = DOAction('Zmove2')
        DOQueue.put(an_action)
        StagebackQueue.get()
        
    def XUP(self):
        an_action = DOAction('XUP')
        DOQueue.put(an_action)
        
        StagebackQueue.get()
    def YUP(self):
        an_action = DOAction('YUP')
        DOQueue.put(an_action)
        StagebackQueue.get()
    def ZUP(self):
        an_action = DOAction('ZUP')
        DOQueue.put(an_action)
        StagebackQueue.get()
        
    def XDOWN(self):
        an_action = DOAction('XDOWN')
        DOQueue.put(an_action)
        StagebackQueue.get()
    def YDOWN(self):
        an_action = DOAction('YDOWN')
        DOQueue.put(an_action)
        StagebackQueue.get()
    def ZDOWN(self):
        an_action = DOAction('ZDOWN')
        DOQueue.put(an_action)
        StagebackQueue.get()
    
    
    def closeEvent(self, event):
        print('Exiting all threads')
        self.Stop_allThreads()
        settings = qc.QSettings("config.ini", qc.QSettings.IniFormat)
        self.SaveSettings()
        if self.Camera_thread.isFinished:
            event.accept()
        else:
            event.ignore()
            
if __name__ == '__main__':
    app = QApplication(sys.argv)
    example = GUI()
    example.show()
    sys.exit(app.exec_())
