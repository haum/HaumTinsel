#!/usr/bin/env python

import time

import numpy as np
import sacn


class LedController:

    def __init__(self):
        self.fill()

        self.sender = sacn.sACNsender(source_name='On vous poutre tous')
        self.sender.start()
        self.sender.activate_output(1)
        self.sender.activate_output(2)
        self.sender[1].multicast = True
        self.sender[2].multicast = True

    def fill(self, val=[0]*3):
        self.chans = val*64*3

    def stop(self):
        self.fill()
        self.blit()
        self.sender.stop()

    def __setitem__(self, k, v):
        self.chans[k*3:(k+1)*3] = v

    def blit(self):
        self.sender[1].dmx_data = self.chans[:510]
        self.sender[2].dmx_data = self.chans[510:]


class TalController:

    def __init__(self):
        self.leds = LedController()

    def __setitem__(self, k, v):
        for l in range(3):
            self.leds[k*3+l] = v


class CubeController:

    def __init__(self):

        self.tals = TalController()
        self.m = np.array([1,35,38,40,15,25,33,32,18,23,28,31,20,21,22,30,55,45,43,41,5,2,36,39,13,16,26,34,12,19,24,29,58,53,48,42,63,56,46,44,8,6,3,37,11,14,17,27,60,52,51,50,61,59,54,49,62,64,57,47,10,9,7,4]).reshape(4,4,4)
        self.autoblit = True

    def __setitem__(self, k, v):
        self.tals[self.m[k]-1] = v
        if self.autoblit: self.blit()

    def fill(self, val=[0]*3):
        self.tals.leds.fill(val)
        if self.autoblit: self.blit()

    def blit(self):
        self.tals.leds.blit()

    def stop(self):
        self.tals.leds.stop()
