# -*- coding: utf-8 -*-
"""
Created on Wed Oct 16 10:51:02 2024

@author: admin
"""

# pyuic5 -o my_ui.py my_ui.ui
try:
    import amcam
    camera_sim = None
except:
    print('no camera driver, using simulation')
    camera_sim = 1

    
import ctypes, sys, time
from PyQt5.QtCore import  QThread
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import *
import numpy as np
from qimage2ndarray import *
import traceback
from Generaic_functions import *
from libtiff import TIFF
import qimage2ndarray as qpy

ptr_uint = ctypes.POINTER(ctypes.c_uint)

import os

class Camera(QThread):
    eventImage = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.hcam = None
        self.buf = None      # video buffer
        self.w = 0           # video width
        self.h = 0           # video height
        self.sliceNum = 0
        self.saved = 0
        x = ctypes.c_uint(42)
        self.p = ptr_uint(x)
        if camera_sim is None:
            self.initCamera()
            if self.hcam is not None:
                self.hcam.put_MaxAutoExpoTimeAGain(1000000,500)
                self.hcam.put_AutoExpoEnable(False)
                # self.SetExposure()
            
    def run(self):
        self.QueueOut()
        
    def QueueOut(self):
        num = 0
        self.item = self.queue.get()
        while self.item.action != 'exit':
            # start=time.time()
            #self.ui.statusbar.showMessage('Display thread is doing ' + self.item.action)
            try:
                if self.item.action in ['Snap']:
                    self.Snap()

                elif self.item.action in ['Live']:
                    self.Live()

                elif self.item.action in ['SetExposure']:
                    self.SetExposure() 
                
                elif self.item.action in ['GetExposure']:
                    self.GetExposure()
                
                elif self.item.action in ['AutoExposure']:
                    self.AutoExposure()
                    
                elif self.item.action in ['InitSaveCount']:
                    self.saved = 0
                
                elif self.item.action in ['Init_Mosaic']:
                    self.Init_Mosaic(self.item.args)
                    
                elif self.item.action in ['Display_Mosaic']:
                    self.Display_Mosaic(self.item.args)
                    
                elif self.item.action in ['Save_Mosaic']:
                    self.Save_Mosaic()
                    
                else:
                    message = 'Camera thread is doing something invalid' + self.item.action
                    self.ui.statusbar.showMessage(message)
                    # self.ui.PrintOut.append(message)
                    self.log.write(message)
                # if time.time()-start>4:
                #     print('time for DnS:',time.time()-start)
            except Exception as error:
                message = "\nAn error occurred:"+" skip the display and save action\n"
                print(message)
                self.ui.statusbar.showMessage(message)
                # self.ui.PrintOut.append(message)
                self.log.write(message)
                print(traceback.format_exc())
            num+=1
            # print(num, 'th display\n')
            self.item = self.queue.get()
        self.Close()
        self.ui.statusbar.showMessage("Camera Thread successfully exited...")

# the vast majority of callbacks come from amcam.dll/so/dylib internal threads, so we use qt signal to post this event to the UI thread  
    @staticmethod
    def cameraCallback(nEvent, ctx):
        if nEvent == amcam.AMCAM_EVENT_IMAGE:
        # if nEvent == amcam.AMCAM_FLAG_TRIGGER_SINGLE:
            ctx.eventImage.emit()
            

# run in the UI thread
# acquire an image and display and save
    @pyqtSlot()
    def eventImageSignal(self):
        if self.hcam is not None:
            try:
                self.hcam.PullImageV2(self.buf, 24, None)
            except amcam.HRESULTException as ex:
                print('pull image failed, hr=0x{:x}'.format(ex.hr))
            else:
                # self.setWindowTitle('{}: {}'.format(self.camname, self.total))
                self.image = np.frombuffer(self.buf, dtype=np.uint8).reshape([self.h,self.w,3])
                pixmap = ImagePlot(self.image)
                self.ui.Image.clear()
                self.ui.Image.setPixmap(pixmap)
                # img = QImage(self.buf, self.w, self.h, (self.w * 24 + 31) // 32 * 4, QImage.Format_RGB888)
                # self.ui.Image.setPixmap(QPixmap.fromImage(img))
                if self.ui.Save.isChecked():
                    self.saved += 1
                    # img.save(self.ui.DIR.toPlainText()+"/"+str(self.sliceNum)+'-'+str(self.saved)+".tiff", "TIFF")
                    pixmap.save(self.ui.DIR.toPlainText()+"/"+str(self.sliceNum)+'-'+str(self.saved).zfill(3)+".tif", "TIFF")

                self.ui.CurrentExpo.setValue(self.hcam.get_ExpoTime()/1000)
                self.ui.statusbar.showMessage('Image taken')
                # if self.callback:
                #     self.CBackQueue.put(0)
                
    def initCamera(self):
        if camera_sim is None:
            a = amcam.Amcam.EnumV2()
            if len(a) <= 0:
                print("No camera found")
                self.hcam = None
                self.ui.autoExposure.setEnabled(False)
            else:
                self.camname = a[0].displayname
                self.eventImage.connect(self.eventImageSignal)
                
                try:
                    self.hcam = amcam.Amcam.Open(a[0].id)
                    self.hcam.put_Option(amcam.AMCAM_OPTION_TRIGGER, 1) # setting software trigger
                    # print('exposure time: ',self.hcam.get_ExpoTime())
                    # print('Gain: ',self.hcam.get_ExpoAGain())
                except amcam.HRESULTException as ex:
                    print(ex)
                else:
                    self.w, self.h = self.hcam.get_Size()
                    bufsize = ((self.w * 24 + 31) // 32 * 4) * self.h
                    self.buf = bytes(bufsize)         
                    try:
                        if sys.platform == 'win32':
                            self.hcam.put_Option(amcam.AMCAM_OPTION_BYTEORDER, 0) # QImage.Format_RGB888
                        self.hcam.StartPullModeWithCallback(self.cameraCallback, self)
                    except amcam.HRESULTException as ex:
                        print('failed to start camera, hr=0x{:x}'.format(ex.hr))
                    
    def Snap(self):
        if self.hcam is not None:
            self.hcam.put_Option(amcam.AMCAM_OPTION_TRIGGER, 1) # setting software trigger
            # self.SetExposure()
            self.hcam.Trigger(1)
            self.callback = 1
            # time.sleep(0.1)
            # self.CQueueback.put(0)
        
    def Live(self):
        if self.hcam is not None:
            self.callback = 0
            if self.ui.LiveButton.isChecked():
                self.ui.LiveButton.setText('Stop')
                self.hcam.put_Option(amcam.AMCAM_OPTION_TRIGGER, 0) # setting software trigger
            else:
                self.ui.LiveButton.setText('Live')
                self.hcam.put_Option(amcam.AMCAM_OPTION_TRIGGER, 1) # setting software trigger

                    
    def SetExposure(self):
        if self.hcam is not None:
            self.hcam.put_ExpoTime(np.uint16(self.ui.Exposure.value()*1000))
            # self.ui.Expo.setText(str(self.hcam.get_ExpoTime()/1000))
            # self.hcam.put_ExpoAGain(100)
            
    def GetExposure(self):
        if self.hcam is not None:
            return self.hcam.get_ExpoTime()/1000

            
    def AutoExposure(self):
        if self.hcam is not None:
            if self.ui.AutoExpo.isChecked():
                self.hcam.put_AutoExpoEnable(True)
            else:
                self.hcam.put_AutoExpoEnable(False)
                self.ui.Exposure.setValue(self.ui.CurrentExpo.value())
        
    def Init_Mosaic(self, args = []):
        
        Xtiles = args[1][0]
        Ytiles = args[1][1]
        # adjust scale ###################
        self.scale = 20

        ###############
        self.surf = np.zeros([ Ytiles*(self.h//self.scale),Xtiles*(self.w//self.scale),3],dtype = np.uint8)
        print(self.surf.shape)
        pixmap = ImagePlot(self.surf)
        # clear content on the waveformLabel
        self.ui.Mosaic.clear()
        # update iamge on the waveformLabel
        self.ui.Mosaic.setPixmap(pixmap)
        self.sliceNum += 1
        
        filename = 'slice-'+str(self.sliceNum)+'-Tiles X-'+str(Xtiles)+'-by Y-'+str(Ytiles)+'-.bin'
        filePath = self.ui.DIR.toPlainText()
        filePath = filePath + "/" + filename
        # print(filePath)
        fp = open(filePath, 'wb')
        fp.close()
    
    def Display_Mosaic(self, args = []):
        # for odd strips, need to flip data in Y dimension and also the sequence
        Xtiles = args[1][0]
        Ytiles = args[1][1]

        Y = Ytiles-args[0][1]-1
        if np.mod(args[0][1],2) == 0:
            X = args[0][0]
        else:
            X = Xtiles - args[0][0]-1
        print('X:',X,' Y:', Y)
        self.surf[self.h//self.scale*Y:self.h//self.scale*(Y+1),\
                  self.w//self.scale*X:self.w//self.scale*(X+1)] = self.image[::self.scale,::self.scale,:]
        
        pixmap = ImagePlot(self.surf)
        self.ui.Mosaic.clear()
        self.ui.Mosaic.setPixmap(pixmap)
        
    def Save_Mosaic(self):
        if self.ui.Save.isChecked():
            pixmap = ImagePlot(self.surf)
            pixmap.save(self.ui.DIR.toPlainText()+'/slice'+str(self.sliceNum)+'coase.tif', "TIFF")
            
            
    def Close(self):
        if self.hcam is not None:
            self.hcam.Close()
            self.hcam = None
            