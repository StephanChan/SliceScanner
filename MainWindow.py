# -*- coding: utf-8 -*-
"""
Created on Wed Oct 16 16:23:15 2024

@author: admin
"""

# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 16:35:04 2023

@author: admin
"""

from my_ui import Ui_MainWindow
import os
from PyQt5 import QtWidgets as QW
from PyQt5.QtWidgets import  QMainWindow, QFileDialog, QWidget, QVBoxLayout

import PyQt5.QtCore as qc
import numpy as np
from Actions import *
from Generaic_functions import *
import traceback

from traits.api import HasTraits, Instance, on_trait_change
from traitsui.api import View, Item


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.LoadSettings()
        self.setStageMinMax() 
        #################### load configuration settings

        self.update_Mosaic()
        self.connectActions()
        
    def setStageMinMax(self):
        self.ui.XPosition.setMinimum(self.ui.Xmin.value())
        self.ui.XPosition.setMaximum(self.ui.Xmax.value())
        
        self.ui.YPosition.setMinimum(self.ui.Ymin.value())
        self.ui.YPosition.setMaximum(self.ui.Ymax.value())
        
        # self.ui.ZPosition.setMinimum(self.ui.Zmin.value())
        # self.ui.ZPosition.setMaximum(self.ui.Zmax.value())
        
        
    def LoadSettings(self):
        settings = qc.QSettings("config.ini", qc.QSettings.IniFormat)
        for ii in dir(self.ui):
            if ii == 'ACQMode':
                pass
            elif type(self.ui.__getattribute__(ii)) == QW.QComboBox:
                try:
                    self.ui.__getattribute__(ii).setCurrentText(settings.value(ii))
                except:
                    print(ii, ' setting missing, using default...')
            elif type(self.ui.__getattribute__(ii)) == QW.QDoubleSpinBox:
                try:
                    self.ui.__getattribute__(ii).setValue(np.float32(settings.value(ii)))
                except:
                    print(ii, ' setting missing, using default...')
            elif type(self.ui.__getattribute__(ii)) == QW.QSpinBox:
                try:
                    self.ui.__getattribute__(ii).setValue(np.int16(settings.value(ii)))
                except:
                    print(ii, ' setting missing, using default...')
            elif type(self.ui.__getattribute__(ii)) == QW.QTextEdit:
                try:
                    self.ui.__getattribute__(ii).setText(settings.value(ii))
                except:
                    print(ii, ' setting missing, using default...')
            elif type(self.ui.__getattribute__(ii)) == QW.QLineEdit:
                try:
                    self.ui.__getattribute__(ii).setText(settings.value(ii))
                except:
                    print(ii, ' setting missing, using default...')
            elif type(self.ui.__getattribute__(ii)) == QW.QPushButton:
                try:
                    self.ui.__getattribute__(ii).setChecked(settings.value(ii))
                except:
                    print(ii, ' setting missing, using default...')
                
    def SaveSettings(self):
        settings = qc.QSettings("config.ini", qc.QSettings.IniFormat)
        for ii in dir(self.ui):
            if type(self.ui.__getattribute__(ii)) == QW.QComboBox:
                settings.setValue(ii,self.ui.__getattribute__(ii).currentText())
            elif type(self.ui.__getattribute__(ii)) == QW.QDoubleSpinBox:
                settings.setValue(ii,self.ui.__getattribute__(ii).value())
            elif type(self.ui.__getattribute__(ii)) == QW.QSpinBox:
                settings.setValue(ii,self.ui.__getattribute__(ii).value())
            elif type(self.ui.__getattribute__(ii)) == QW.QTextEdit:
                settings.setValue(ii,self.ui.__getattribute__(ii).toPlainText())
            elif type(self.ui.__getattribute__(ii)) == QW.QLineEdit:
                settings.setValue(ii,self.ui.__getattribute__(ii).text())
            elif type(self.ui.__getattribute__(ii)) == QW.QPushButton:
                settings.setValue(ii,self.ui.__getattribute__(ii).isChecked())
            
    def connectActions(self):
        
        self.ui.XStart.valueChanged.connect(self.update_Mosaic)
        self.ui.XStop.valueChanged.connect(self.update_Mosaic)
        self.ui.YStart.valueChanged.connect(self.update_Mosaic)
        self.ui.YStop.valueChanged.connect(self.update_Mosaic)
        self.ui.Overlap.valueChanged.connect(self.update_Mosaic)
        

        self.ui.Xmax.valueChanged.connect(self.setStageMinMax)
        self.ui.Xmin.valueChanged.connect(self.setStageMinMax)
        self.ui.Ymin.valueChanged.connect(self.setStageMinMax)
        self.ui.Ymax.valueChanged.connect(self.setStageMinMax)
        self.ui.YFOV.valueChanged.connect(self.setStageMinMax)
        self.ui.XFOV.valueChanged.connect(self.setStageMinMax)
        self.ui.Save.clicked.connect(self.chooseDir)
        # self.ui.Zmin.valueChanged.connect(self.setStageMinMax)
        # self.ui.Zmax.valueChanged.connect(self.setStageMinMax)


    def chooseDir(self):
        if self.ui.Save.isChecked():
            
             dir_choose = QFileDialog.getExistingDirectory(self,  
                                         "选取文件夹",  
                                         os.getcwd()) # 起始路径
        
             if dir_choose == "":
                 print("\n取消选择")
                 return
             self.ui.DIR.setText(dir_choose)
             
    def LoadConfig(self):
        fileName_choose, filetype = QFileDialog.getOpenFileName(self,  
                                   "选取文件",  
                                   os.getcwd(), # 起始路径 
                                   "All Files (*);;Text Files (*.txt)")   # 设置文件扩展名过滤,用双分号间隔

        if fileName_choose == "":
           print("\n取消选择")
           return
        settings = qc.QSettings(fileName_choose, qc.QSettings.IniFormat)
        
        try:
            self.load_settings(settings)
        except Exception as error:
            print('settings reload failed, using default settings')
            print(traceback.format_exc())
        
        
    def update_Mosaic(self):
        self.Mosaic_pattern, status = GenMosaic_XYGalvo(self.ui.XStart.value(),\
                                        self.ui.XStop.value(),\
                                        self.ui.YStart.value(),\
                                        self.ui.YStop.value(),\
                                        self.ui.XFOV.value(),\
                                        self.ui.YFOV.value(),\
                                        self.ui.Overlap.value())
        # get total number of strips, i.e.，xstage positions
        total_X = self.Mosaic_pattern.shape[1]
        total_Y = self.Mosaic_pattern.shape[2]

        self.totalTiles = total_X*total_Y
        
        self.Mosaic_pattern = self.Mosaic_pattern.reshape(2,total_X*total_Y)
        self.ui.statusbar.showMessage(status)
        if self.Mosaic_pattern is not None:
            
                
            pixmap = ScatterPlot(self.Mosaic_pattern)
            # clear content on the waveformLabel
            self.ui.MosaicLabel.clear()
            # update iamge on the waveformLabel
            self.ui.MosaicLabel.setPixmap(pixmap)

    
        
        