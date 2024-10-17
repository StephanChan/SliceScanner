# -*- coding: utf-8 -*-
"""
Created on Wed Jan 24 11:10:17 2024

@author: admin
"""

#################################################################
# THIS KING THREAD IS USING ART8912, WHICH IS MASTER AND the DO board WILL BE SLAVE
from PyQt5.QtCore import  QThread
from PyQt5.QtWidgets import QDialog
import time
import numpy as np
from Generaic_functions import *
from Actions import DOAction, CAction
import traceback
import os
import datetime


class WeaverThread(QThread):
    def __init__(self):
        super().__init__()
        
        self.mosaic = None
        self.exit_message = 'weaver thread successfully exited'
        
    def run(self):
        # self.InitMemory()
        self.QueueOut()
        
    def QueueOut(self):
        self.item = self.queue.get()
        while self.item.action != 'exit':
            # self.ui.statusbar.showMessage('King thread is doing: '+self.item.action)
            try:
                if self.item.action in ['Mosaic']:
                    message = self.Mosaic()
                    self.ui.statusbar.showMessage(message)
                    # self.ui.PrintOut.append(message)
                    self.log.write(message)
                    self.ui.MosaicButton.setChecked(False)
                    self.ui.MosaicButton.setText('Mosaic')
                    self.ui.PauseButton.setChecked(False)
                    self.ui.PauseButton.setText('Pause')

            except Exception as error:
                message = "An error occurred,"+"skip the acquisition action\n"
                self.ui.statusbar.showMessage(message)
                # self.ui.PrintOut.append(message)
                self.log.write(message)
                print(traceback.format_exc())
            self.item = self.queue.get()
            
        self.ui.statusbar.showMessage(self.exit_message)
            
    
  
    def Mosaic(self):
        # slice number increase, tile number restart from 1
        an_action = CAction('InitSaveCount') # data in Memory[memoryLoc]
        self.CQueue.put(an_action)

        self.Mosaic_pattern, status = GenMosaic_XYGalvo(self.ui.XStart.value(),\
                                        self.ui.XStop.value(),\
                                        self.ui.YStart.value(),\
                                        self.ui.YStop.value(),\
                                        self.ui.XFOV.value(),\
                                        self.ui.YFOV.value(),\
                                        self.ui.Overlap.value())
        # get total number of strips, i.e.，xstage positions
        total_Y = self.Mosaic_pattern.shape[1]
        total_X = self.Mosaic_pattern.shape[2]

        self.Mosaic_pattern_flattern = self.Mosaic_pattern.reshape(2,total_X*total_Y)
        # init sample surface plot window
        args = [[0,0],[total_X, total_Y]]
        an_action = CAction('Init_Mosaic', args = args) # data in Memory[memoryLoc]
        self.CQueue.put(an_action)
        
        # init local variables
        interrupt = None
        ############################################################# Iterate through strips for one Mosaic
        for yy in range(total_Y):
            for xx in range(total_X):
                if interrupt != 'Stop':
                    # stage move to start XYZ position
                    self.ui.XPosition.setValue(self.Mosaic_pattern[0,yy,xx])
                    an_action = DOAction('Xmove2')
                    self.DOQueue.put(an_action)
                    self.StagebackQueue.get()
                    self.ui.YPosition.setValue(self.Mosaic_pattern[1,yy,xx])
                    an_action = DOAction('Ymove2')
                    self.DOQueue.put(an_action)
                    self.StagebackQueue.get()

                    an_action = CAction('Snap')
                    self.CQueue.put(an_action)
                    time.sleep(0.5)
                    # self.CBackQueue.get()
                    
                    # update mosaic pattern
                    self.Mosaic_pattern_flattern = self.Mosaic_pattern_flattern[:,1:]
                    pixmap = ScatterPlot(self.Mosaic_pattern_flattern)
                    # clear content on the waveformLabel
                    self.ui.MosaicLabel.clear()
                    # update iamge on the waveformLabel
                    self.ui.MosaicLabel.setPixmap(pixmap)
                    ############################ check user input
                    interrupt = self.check_interrupt()
                
                
                    an_action = CAction('Display_Mosaic', args = [[xx,yy],[total_X, total_Y]]) 
                    self.CQueue.put(an_action)  
        an_action = CAction('Save_Mosaic') 
        self.CQueue.put(an_action)
        return 'Mosaic successfully finished...'
    
    def check_interrupt(self):
        interrupt = None
        try:
            # check if Pause button is clicked
           interrupt = self.PauseQueue.get_nowait()  # time out 0.001 s
           # print(interrupt)
           ##################################### if Pause button is clicked
           if interrupt == 'Pause':
               # self.ui.PauseButton.setChecked(True)
               # wait until unpause button or stop button is clicked
               interrupt = self.PauseQueue.get()  # never time out
               # print('queue output:',interrupt)
               # if unpause button is clicked        
               if interrupt == 'Resume':
                   # self.ui.PauseButton.setChecked(False)
                   interrupt = None
        except:
            return interrupt
        return interrupt
        
    