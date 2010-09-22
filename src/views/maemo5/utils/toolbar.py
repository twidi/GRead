# -*- coding: utf-8 -*-

"""
Lib to manage toolbars which appear on mousedown and stay visible a few seconds
"""
from PyQt4.QtGui import *
from PyQt4.QtCore import *

from ...basic.utils.toolbar import ToolbarManager as BasicToolbarManager

class ToolbarManager(BasicToolbarManager):
    
    def __init__(self, *args, **kwargs):
        super(ToolbarManager, self).__init__(*args, **kwargs)
        self.max_delay = 1500.0 # ms (don't forget ".0")
        self.event_target.installEventFilter(self)            

    def eventFilter(self, obj, e):
        if e.type() == QEvent.HoverMove:
            if self.delay and self.delay < 500:
                self.display()
            elif (not self.delay):
                self.display()                
        return False


