# -*- coding: utf-8 -*-
"""
Created on Mon Dec 11 19:41:46 2023

@author: admin
"""
# DO configure: port0 line 0 for X stage, port0 line 1 for Y stage, port 0 line 2 for Z stage, port 0 line 3 for Digitizer enable

# Generating Galvo X direction waveforms based on step size, Xsteps, Aline averages and objective
# StepSize in unit of um
# bias in unit of mm
global STEPS
STEPS = 25000
# 2mm per revolve
global DISTANCE
DISTANCE = 2
# scan direction suring Cscan is Y axis

import numpy as np

import os

class LOG():
    def __init__(self, ui):
        super().__init__()
        import datetime
        current_time = datetime.datetime.now()
        self.dir = os.getcwd() + '/log_files'
        if not os.path.exists(self.dir):
            os.makedirs(self.dir)
        self.filePath = self.dir +  "/" + 'log_'+\
            str(current_time.year)+'-'+\
            str(current_time.month)+'-'+\
            str(current_time.day)+'-'+\
            str(current_time.hour)+'-'+\
            str(current_time.minute)+'-'+\
            str(current_time.second)+'.txt'
    def write(self, message):
        fp = open(self.filePath, 'a')
        fp.write(message+'\n')
        fp.close()
        # return 0



def GenStageWave(one_cycle_samples, Aline_frq, stageSpeed):
    # generate DO waveforms for moving stage
    if stageSpeed > 0.00001:
            time = one_cycle_samples/Aline_frq # time for one bline
            distance = time*stageSpeed # mm to move
            print(distance,'mm')
            steps = distance / DISTANCE * STEPS # how many steps needed to reach that distance
            stride = np.uint16(one_cycle_samples/steps)
            print(steps, stride)
            stagewaveform = np.zeros(one_cycle_samples)
            for ii in range(0,one_cycle_samples,stride):
                stagewaveform[ii] = 1
            return stagewaveform
    else:
        stagewaveform = np.zeros(one_cycle_samples)
        return stagewaveform

def GenStageWave_ramp(distance, AlineTriggers):
    # distance: stage movement per Cscan , mm/s
    # edges: Aline triggers
    # how many motor steps to reach that distance
    steps = (distance/DISTANCE*STEPS)
    # how many Aline triggers per motor step
    clocks_per_motor_step = np.int16(AlineTriggers/steps)
    if clocks_per_motor_step < 2:
        clocks_per_motor_step = 2
    # print('clocks per motor step: ',clocks_per_motor_step)
    # generate stage movement that ramps up and down speed so that motor won't miss signal at beginning and end
    # ramping up: the interval between two steps should be 100 clocks at the beginning, then gradually decrease.vice versa for ramping down
    if np.abs(distance) > 0.01:
        max_interval = 80
    else:
        max_interval = 40
    # the interval for ramping up and down
    ramp_up_interval = np.arange(max_interval,clocks_per_motor_step,-2)
    ramp_down_interval = np.arange(clocks_per_motor_step,max_interval+1,2)
    ramping_steps = np.sum(len(ramp_down_interval)+len(ramp_up_interval)) # number steps used in ramping up and down process
    
    # ramping up waveform generation
    ramp_up_waveform = np.zeros(np.sum(ramp_up_interval))
    if any(ramp_up_waveform):
        ramp_up_waveform[0] = 1
    time_lapse = -1
    for interval in ramp_up_interval:
        time_lapse = time_lapse + interval
        ramp_up_waveform[time_lapse] = 1

    # ramping down waveform generation
    ramp_down_waveform = np.zeros(np.sum(ramp_down_interval))
    if any(ramp_down_waveform):
        ramp_down_waveform[0] = 1
    time_lapse = -1
    for interval in ramp_down_interval:
        time_lapse = time_lapse + interval
        ramp_down_waveform[time_lapse] = 1
        
    # normal speed waveform
    steps_left = steps - ramping_steps
    clocks_left = np.int32(AlineTriggers-len(ramp_down_waveform)-len(ramp_up_waveform))
    stride = np.int16(clocks_left/steps_left)
    if stride < 2:
        stride = 2
    clocks_left = np.int32(steps_left * stride)
    stagewaveform = np.zeros(clocks_left)
    for ii in range(0,clocks_left,stride):
        stagewaveform[ii] = 1
    
    # append all arrays
    DOwaveform = np.append(ramp_up_waveform,stagewaveform)
    DOwaveform = np.append(DOwaveform,ramp_down_waveform)
    if len(DOwaveform) < AlineTriggers:
        DOwaveform = np.append(DOwaveform,np.zeros(AlineTriggers-len(DOwaveform),dtype = np.int16))
    return DOwaveform

def GenAODO(mode='RptBline', Aline_frq = 100000, XStepSize = 1, XSteps = 1000, AVG = 1, bias = 0, obj = 'OptoSigma5X',\
            preclocks = 50, postclocks = 200, YStepSize = 1, YSteps = 200, BVG = 1):
    # DO clock is swept source A-line trigger at 100kHz
    # DO configure: port0 line 0 for X stage, port0 line 1 for Y stage, port 0 line 2 for Z stage, port 0 line 3 for Digitizer enable
    if mode == 'RptAline' or mode == 'SingleAline':
        # RptAline is for checking Aline profile, we don't need to capture each Aline, only display 30 Alines per second\
        # if one wants to capture each Aline, they can set X and Y step size to be 0 and capture Cscan instead
        # 33 frames per second, how many samples for each frame
        one_cycle_samples = XSteps * AVG + 2 * preclocks + postclocks
        # trigger enbale waveform generation
        DOwaveform = np.append(np.zeros(preclocks), pow(2,ATSenable)*np.ones(XSteps * AVG))
        DOwaveform = np.append(DOwaveform, np.zeros(preclocks + postclocks))
        CscanAO = np.ones(BVG*len(DOwaveform)) * Galvo_bias
        CscanDO = np.zeros(BVG*len(DOwaveform))
        for ii in range(BVG):
            CscanDO[ii*len(DOwaveform):(ii+1)*len(DOwaveform)] = DOwaveform
        status = 'waveform updated'
        return np.uint32(CscanDO), CscanAO, status
    
    elif mode == 'RptBline' or mode == 'SingleBline':
        # RptBline is for checking Bline profile, only display 30 Blines per second
        # if one wants to capture each Bline, they can set Y stepsize to be 0 and capture Cscan instead
        # generate AO waveform for Galvo control
        AOwaveform, status = GenGalvoWave(XStepSize, XSteps, AVG, bias, obj, preclocks, postclocks)
        
        # total number of Alines
        one_cycle_samples = XSteps*AVG
        # generate trigger waveforms
        DOwaveform = np.append(np.zeros(preclocks), pow(2,ATSenable)*np.ones(one_cycle_samples))
        DOwaveform = np.append(DOwaveform, np.zeros(preclocks+postclocks))
        CscanAO = np.zeros(BVG*len(AOwaveform))
        CscanDO = np.zeros(BVG*len(DOwaveform))
        for ii in range(BVG):
            CscanAO[ii*len(AOwaveform):(ii+1)*len(AOwaveform)] = AOwaveform
            CscanDO[ii*len(AOwaveform):(ii+1)*len(AOwaveform)] = DOwaveform
        status = 'waveform updated'
        return np.uint32(CscanDO), CscanAO, status
    
    
    elif mode in ['SingleCscan','Mosaic','Mosaic+Cut']:
            # # RptCscan is for acquiring Cscan at the same location repeatitively
            # # generate AO waveform for Galvo control for one Bline
            # AOwaveform, status = GenGalvoWave(XStepSize, XSteps, AVG, bias, obj, preclocks, postclocks)
            # # total number of Alines
            # one_cycle_samples = XSteps * AVG
            # # generate trigger waveforms
            # DOwaveform = np.append(np.zeros(preclocks), pow(2,3)*np.zeros(one_cycle_samples))
            # DOwaveform = np.append(DOwaveform, np.zeros(preclocks+postclocks))
            # # calculate stage speed for Cscan
            # stageSpeed=YStepSize/1000.0/(one_cycle_samples/Aline_frq) # unit: mm/s
            # # generate stage control waveforms for one step
            # print(one_cycle_samples, Aline_frq, stageSpeed)
            # stagewaveform = GenStageWave(one_cycle_samples, Aline_frq, stageSpeed)
            # # append preclocks and postclocks
            # stagewaveform = np.append(np.zeros(preclocks), pow(2,CSCAN_AXIS)*stagewaveform)
            # stagewaveform = np.append(stagewaveform, np.zeros(preclocks+postclocks))
            # print('distance per Bline: ',np.sum(stagewaveform)/STEPS*DISTANCE*1000/pow(2,CSCAN_AXIS),'um')
            # # add stagewaveform with trigger enable waveform for DOwaveform
            # DOwaveform = DOwaveform + stagewaveform
            # # repeat the waveform for whole Cscan
            # CscanAO = np.zeros(YSteps*BVG*len(AOwaveform))
            # CscanDO = np.zeros(YSteps*BVG*len(DOwaveform))
            # for ii in range(YSteps*BVG):
            #     CscanAO[ii*len(AOwaveform):(ii+1)*len(AOwaveform)] = AOwaveform
            #     CscanDO[ii*len(AOwaveform):(ii+1)*len(AOwaveform)] = DOwaveform
            # status = 'waveform updated'
            # return np.uint32(CscanDO), CscanAO, status
        # RptCscan is for acquiring Cscan at the same location repeatitively
        # generate AO waveform for Galvo control for one Bline
        AOwaveform, status = GenGalvoWave(XStepSize, XSteps, AVG, bias, obj, preclocks, postclocks)
        CscanAO = np.zeros(YSteps*BVG*len(AOwaveform))
        for ii in range(YSteps*BVG):
            CscanAO[ii*len(AOwaveform):(ii+1)*len(AOwaveform)] = AOwaveform
        # total number of Alines per Bline
        one_cycle_samples = XSteps * AVG
        # generate trigger waveforms
        DOwaveform = np.append(np.zeros(preclocks), pow(2,ATSenable)*np.zeros(one_cycle_samples))
        DOwaveform = np.append(DOwaveform, np.zeros(preclocks+postclocks))
        
        CscanDO = np.zeros(YSteps*BVG*len(DOwaveform))
        for ii in range(YSteps*BVG):
            CscanDO[ii*len(DOwaveform):(ii+1)*len(DOwaveform)] = DOwaveform
            
        stagewaveform = GenStageWave_ramp(YSteps * YStepSize/1000, (XSteps*AVG + 2 * preclocks + postclocks)* YSteps * BVG)
        # append preclocks and postclocks
        stagewaveform = pow(2,CSCAN_AXIS)*stagewaveform
        # print('distance per Cscan: ',np.sum(stagewaveform)/STEPS*DISTANCE*1000/pow(2,CSCAN_AXIS),'um')
        # add stagewaveform with trigger enable waveform for DOwaveform
        if len(stagewaveform) > len(CscanDO):
            CscanDO = np.append(CscanDO, np.zeros(len(stagewaveform)-len(CscanDO), dtype = np.uint32))
            CscanAO = np.append(CscanAO, CscanAO[-1]*np.ones(len(stagewaveform)-len(CscanAO), dtype = np.uint32))
        CscanDO = CscanDO + stagewaveform
        # repeat the waveform for whole Cscan
        
        status = 'waveform updated'
        return np.uint32(CscanDO), CscanAO, status
    
    else:
        status = 'invalid task type! Abort action'
        return None, None, status
    

def GenMosaic_XYGalvo(Xmin, Xmax, Ymin, Ymax, XFOV, YFOV, overlap=10):
    # all arguments are with units mm
    # overlap is with unit %
    if Xmin > Xmax:
        status = 'Xmin is larger than Xmax, Mosaic generation failed'
        return None, status
    if Ymin > Ymax:
        status = 'Y min is larger than Ymax, Mosaic generation failed'
        return None, status
    # get FOV step size
    Xstepsize = XFOV*(1-overlap/100)
    # get how many FOVs in X direction
    Xsteps = np.ceil((Xmax-Xmin)/Xstepsize)
    # get actual X range
    actualX=Xsteps*Xstepsize
    # generate start and stop position in X direction
    # add or subtract a small number to avoid precision loss
    startX=Xmin-(actualX-(Xmax-Xmin))/2
    stopX = Xmax+(actualX-(Xmax-Xmin))/2+0.01
    # generate X positions
    Xpositions = np.arange(startX, stopX, Xstepsize)
    #print(Xpositions)
    
    Ystepsize = YFOV*(1-overlap/100)
    Ysteps = np.ceil((Ymax-Ymin)/Ystepsize)
    actualY=Ysteps*Ystepsize
    
    startY=Ymin-(actualY-(Ymax-Ymin))/2
    stopY = Ymax+(actualY-(Ymax-Ymin))/2+0.01
    
    Ypositions = np.arange(startY, stopY, Ystepsize)
    
    Positions = np.array(np.meshgrid(Xpositions, Ypositions))
    status = 'Mosaic Generation success'
    for ii in range(1,len(Ypositions),2):
        Positions[0,ii,:] = np.flip(Positions[0,ii,:])
    
    return Positions, status


from PyQt5.QtGui import QPixmap

from matplotlib import pyplot as plt

def LinePlot(AOwaveform, DOwaveform = None, m=2, M=4):
    # clear content on plot
    plt.cla()
    # plot the new waveform
    plt.plot(range(len(AOwaveform)),AOwaveform,linewidth=2)
    if np.any(DOwaveform):
        plt.plot(range(len(DOwaveform)),(DOwaveform>>3)*np.max(AOwaveform),linewidth=2)
    # plt.ylim(np.min(AOwaveform)-0.2,np.max(AOwaveform)+0.2)
    plt.ylim([m,M])
    plt.xticks(fontsize=15)
    plt.yticks(fontsize=15)
    plt.rcParams['savefig.dpi']=150
    # save plot as jpeg
    plt.savefig('lineplot.jpg')
    # load waveform image
    pixmap = QPixmap('lineplot.jpg')
    return pixmap

def ScatterPlot(mosaic):
    # clear content on plot
    plt.cla()
    # plot the new waveform
    plt.scatter(mosaic[0],mosaic[1])
    plt.plot(mosaic[0],mosaic[1])
    # plt.ylim(-2,2)
    plt.ylabel('Y stage',fontsize=15)
    plt.xlabel('X stage',fontsize=15)
    plt.xticks(fontsize=15)
    plt.yticks(fontsize=15)
    plt.rcParams['savefig.dpi']=150
    # save plot as jpeg
    plt.savefig('scatter.jpg')
    # load waveform image
    pixmap = QPixmap('scatter.jpg')
    return pixmap

import qimage2ndarray as qpy
def ImagePlot(matrix):
    matrix = np.array(matrix)
    im = qpy.array2qimage(matrix)
    pixmap = QPixmap(im)
    return pixmap
    
def findchangept(signal, step):
    # python implementation of matlab function findchangepts
    L = len(signal)
    z = np.argmax(signal)
    last = np.min([z+30,L-2])
    signal = signal[1:last]
    L = len(signal)
    residual_error = np.ones(L)*9999999
    for ii in range(2,L-2,step):
        residual_error[ii] = (ii-1)*np.var(signal[0:ii])+(L-ii+1)*np.var(signal[ii+1:L])
    pts = np.argmin(residual_error)
    # plt.plot(residual_error[2:-2])
    return pts
        