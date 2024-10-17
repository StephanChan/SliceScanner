# pyuic5 -o my_ui.py my_ui.ui
try:
    import amcam
    camera_sim = None
except:
    print('no camera driver, using simulation')
    camera_sim = 1

try:
    import EFW
    EFW_sim = None
except:
    print('no filter driver, using simulation')
    EFW_sim = 1
    
try:
    import DigitalOUT
    DO_sim = None
except:
    print('no DO driver, using simulation')
    DO_sim = 1
    
import ctypes, sys, time
from my_ui import Ui_MainWindow
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import *
import numpy as np
from qimage2ndarray import *

ptr_uint = ctypes.POINTER(ctypes.c_uint)

import os

try:
    os.mkdir(cwd+'\\images')
except:
    pass
class MainWin(QMainWindow):
    eventImage = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.ui=Ui_MainWindow()
        self.ui.setupUi(self)
        self.dir_choose = os.getcwd()
        self.ui.Exposure.valueChanged.connect(self.SetExposure)
        self.ui.SnapButton.clicked.connect(self.SnapClicked)
        self.ui.LiveButton.clicked.connect(self.LiveClicked)
        self.ui.AutoExposure.stateChanged.connect(self.AutoExposure)
        self.ui.checkBox.clicked.connect(self.chooseDIR)
        self.ui.RedButton.clicked.connect(self.RedFilter)
        self.ui.GreenButton.clicked.connect(self.GreenFilter)
        self.ui.RGBbutton1.clicked.connect(self.ND1Filter)
        self.ui.RGBbutton2.clicked.connect(self.ND2Filter)
        self.ui.InitStepper.clicked.connect(self.InitStepper)
        self.ui.StepperUp.clicked.connect(self.StepperUp)
        self.ui.StepperDown.clicked.connect(self.StepperDown)

        self.ui.statusbar.showMessage('initiated')
        self.hcam = None
        self.flt = None
        self.DO = None
        self.buf = None      # video buffer
        self.w = 0           # video width
        self.h = 0           # video height
        self.total = 0
        self.saved = 0
        x = ctypes.c_uint(42)
        self.p = ptr_uint(x)
        if camera_sim is None:
            
            self.initCamera()
            if self.hcam is not None:
                self.hcam.put_MaxAutoExpoTimeAGain(1000000,500)
                self.hcam.put_AutoExpoEnable(False)
                # self.SetExposure()
        if EFW_sim is None:
            self.InitFLT()
            

    def chooseDIR(self):
        if self.ui.checkBox.isChecked():
            self.dir_choose = QFileDialog.getExistingDirectory(self, 'choose saving directory',os.getcwd())
            if self.dir_choose == "":
                print("\n use default directory")
                self.dir_choose = self.ui.saveDIR.toPlainText()
                return
            self.ui.saveDIR.setText(self.dir_choose)

# the vast majority of callbacks come from amcam.dll/so/dylib internal threads, so we use qt signal to post this event to the UI thread  
    @staticmethod
    def cameraCallback(nEvent, ctx):
        if nEvent == amcam.AMCAM_EVENT_IMAGE:
        # if nEvent == amcam.AMCAM_FLAG_TRIGGER_SINGLE:
            ctx.eventImage.emit()
            

# run in the UI thread
    @pyqtSlot()
    def eventImageSignal(self):
        if self.hcam is not None:
            self.ui.statusbar.showMessage('Taking an image...')
            try:
                self.hcam.PullImageV2(self.buf, 24, None)
                self.total += 1
            except amcam.HRESULTException as ex:
                self.ui.statusbar.showMessage('pull image failed, hr=0x{:x}'.format(ex.hr))
            else:
                self.setWindowTitle('{}: {}'.format(self.camname, self.total))
                img = QImage(self.buf, self.w, self.h, (self.w * 24 + 31) // 32 * 4, QImage.Format_RGB888)
                if self.ui.checkBox.isChecked():
                    self.saved += 1
                    img.save(self.dir_choose+"/"+str(self.saved)+".tiff", "TIFF")
                self.ui.ImageLabel.setPixmap(QPixmap.fromImage(img))
                self.ui.ImageLabel.setScaledContents(True)
                self.ui.Expo.setText(str(self.hcam.get_ExpoTime()/1000))
                self.ui.statusbar.showMessage('Image taken')
  
    def SnapClicked(self):
        if self.hcam is not None:
            self.hcam.put_Option(amcam.AMCAM_OPTION_TRIGGER, 1) # setting software trigger
            # self.SetExposure()
            self.hcam.Trigger(1)
        
    def LiveClicked(self):
        if self.hcam is not None:
            # self.hcam.put_ExpoTime(500000)
            if self.ui.LiveButton.isChecked():
                self.ui.LiveButton.setText('Stop live')
                self.hcam.put_Option(amcam.AMCAM_OPTION_TRIGGER, 0) # setting software trigger
            else:
                self.ui.LiveButton.setText('Live')
                self.hcam.put_Option(amcam.AMCAM_OPTION_TRIGGER, 1) # setting software trigger
        
    def SetExposure(self):
        if self.hcam is not None:
            self.hcam.put_ExpoTime(self.ui.Exposure.value())
            self.ui.Expo.setText(str(self.hcam.get_ExpoTime()/1000))
            self.hcam.put_ExpoAGain(100)
        
    def AutoExposure(self):
        if self.hcam is not None:
            if self.ui.AutoExposure.isChecked():
                self.hcam.put_AutoExpoEnable(True)
            else:
                self.hcam.put_AutoExpoEnable(False)
                self.hcam.put_ExpoTime(self.ui.Exposure.value())
        
    def initCamera(self):
        if camera_sim is None:
            a = amcam.Amcam.EnumV2()
            if len(a) <= 0:
                self.setWindowTitle('No camera found')
                print("No camera found")
                self.hcam = None
                # self.ui.autoExposure.setEnabled(False)
            else:
                self.camname = a[0].displayname
                self.setWindowTitle(self.camname)
                self.eventImage.connect(self.eventImageSignal)
                
                try:
                    self.hcam = amcam.Amcam.Open(a[0].id)
                    self.hcam.put_Option(amcam.AMCAM_OPTION_TRIGGER, 1) # setting software trigger
                    # print('exposure time: ',self.hcam.get_ExpoTime())
                    # print('Gain: ',self.hcam.get_ExpoAGain())
                except amcam.HRESULTException as ex:
                    # QMessageBox.warning(self, '', 'failed to open camera, hr=0x{:x}'.format(ex.hr), QMessageBox.Ok)
                    self.ui.statusbar.showMessage('failed to open camera, hr=0x{:x}'.format(ex.hr))
                else:
                    self.w, self.h = self.hcam.get_Size()
                    bufsize = ((self.w * 24 + 31) // 32 * 4) * self.h
                    self.buf = bytes(bufsize)         
                    try:
                        if sys.platform == 'win32':
                            self.hcam.put_Option(amcam.AMCAM_OPTION_BYTEORDER, 0) # QImage.Format_RGB888
                        self.hcam.StartPullModeWithCallback(self.cameraCallback, self)
                    except amcam.HRESULTException as ex:
                        self.ui.statusbar.showMessage('failed to start camera, hr=0x{:x}'.format(ex.hr))
                    
    def InitFLT(self):
        if EFW_sim is None:
            self.flt=EFW.EFWfilter()
            self.devices=self.flt.GetNum()
            if self.devices is not None:
                if self.devices>0:
                    ID = ctypes.c_uint(0)
                    self.ID = ptr_uint(ID)
                    self.flt.GetID(self.devices-1, self.ID)
                    # print(self.ID.contents)
                    self.flt.Open(self.ID.contents)
                    # info=self.EFW._EFW_INFO()
                    info = self.flt.GetProperty(self.ID.contents)
                    # print(info.slotNum)
                    self.ui.statusbar.showMessage('filter wheel successfully loaded')
            else:
                self.flt=None
    def RedFilter(self):
        if self.flt is not None:
            self.flt.SetPosition(self.ID.contents, ctypes.c_uint(0))
            self.ui.RedButton.setText('Using Red')
            self.ui.GreenButton.setText('Green')
            self.ui.RGBbutton1.setText('ND0.5')
            self.ui.RGBbutton2.setText('ND1')
        
    def GreenFilter(self):
        if self.flt is not None:
            self.flt.SetPosition(self.ID.contents, ctypes.c_uint(1))
            self.ui.RedButton.setText('Red')
            self.ui.GreenButton.setText('using Green')
            self.ui.RGBbutton1.setText('ND0.5')
            self.ui.RGBbutton2.setText('ND1')
        
    def ND1Filter(self):
        if self.flt is not None:
            self.flt.SetPosition(self.ID.contents, ctypes.c_uint(2))
            self.ui.RedButton.setText('Red')
            self.ui.GreenButton.setText('Green')
            self.ui.RGBbutton1.setText('using ND0.5')
            self.ui.RGBbutton2.setText('ND1')
        
    def ND2Filter(self):
        if self.flt is not None:
            self.flt.SetPosition(self.ID.contents, ctypes.c_uint(3))
            self.ui.RedButton.setText('Red')
            self.ui.GreenButton.setText('Green')
            self.ui.RGBbutton1.setText('ND0.5')
            self.ui.RGBbutton2.setText('using ND1')
            
    def InitStepper(self):
        if DO_sim is None:
            self.DO=DigitalOUT.DO()
            self.DO.initDO()
            self.EnablePort = self.DO.ports[0]
            self.EnablePin = 0
            self.SpeedPort =  self.DO.ports[0]
            self.SpeedPin = 1
            self.MovePort = self.DO.ports[0]
            self.MovePin = 2
            self.DirectionPort = self.DO.ports[0]
            self.DirectionPin = 3
            # Set enable state to 1
            self.Enable()
            
    def StepperUp(self):
        if self.DO is not None:
            self.DO.SetSpeed(self.SpeedPort, self.SpeedPin, self.ui.StepperSpeed.isChecked())
            self.DO.SetDirection(self.DirectionPort, self.DirectionPin, 1)
            self.DO.Move(self.MovePort, self.MovePin, 1)
            time.sleep(self.ui.StepperTime.value())
            self.DO.Move(self.MovePort, self.MovePin, 0)
            
    def StepperDown(self):
        if self.DO is not None:
            self.DO.SetSpeed(self.SpeedPort, self.SpeedPin, self.ui.StepperSpeed.isChecked())
            self.DO.SetDirection(self.DirectionPort, self.DirectionPin, 0)
            self.DO.Move(self.MovePort, self.MovePin, 1)
            time.sleep(self.ui.StepperTime.value())
            self.DO.Move(self.MovePort, self.MovePin, 0)
            
    def Enable(self):
        if self.DO is not None:
            self.DO.Enable(self.EnablePort, self.EnablePin, 1)
            
    def Disable(self):
        if self.DO is not None:
            self.DO.Enable(self.EnablePort, self.EnablePin, 0)
                
    def closeEvent(self, event):
        if self.hcam is not None:
            self.hcam.Close()
            self.hcam = None
        if self.flt is not None:
            self.flt.Close(self.ID.contents)
            
        if self.DO is not None:
            self.DO.UninitDO()
            self.DO = None

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainWin()
    win.show()
    sys.exit(app.exec_())