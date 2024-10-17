# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 16:43:51 2023

@author: admin
"""
# here defines all the legitimate actions that can be put into a queue

import numpy as np

class DOAction():
    def __init__(self, action, direction = 1):
        super().__init__()
        self.action=action
        self.direction = direction

class WeaverAction():
    def __init__(self, action):
        super().__init__()
        self.action = action
        
        
class CAction():
    def __init__(self, action, args = []):
        super().__init__()
        self.action = action 
        self.args = args
        
class CbackAction():
    def __init__(self, action):
        super().__init__()
        self.action = action 
        
class EXIT():
    def __init__(self):
        super().__init__()
        self.action='exit'
