# -*- coding: utf-8 -*-

"""
Lib to manage toolbars which appear on mousedown(maemo) or mousemove(not maem0)
and stay visible a few seconds
"""
from PyQt4.QtGui import *
from PyQt4.QtCore import *

import time

class ToolbarOwnerEventFilter(QObject):
    def __init__(self, *args, **kwargs):
        super(ToolbarOwnerEventFilter, self).__init__(*args, **kwargs)

    def eventFilter(self, obj, e):
        if e.type() == QEvent.Resize:
            self.parent().replace_toolbars()
        return False
            
            

class ToolbarManager(QObject):
    
    def __init__(self, toolbars,  event_target, *args, **kwargs):
        super(ToolbarManager, self).__init__(*args, **kwargs)

        parent = self.parent()

        self.event_target = event_target
        
        self.toolbars     = toolbars
        self.mode_opacity = False # don't know how to change opacity !
        self.timer        = QTimer()
        self.delay        = 0
        self.max_delay = 1000.0 # ms (don't forget ".0")

        parent.installEventFilter(self)
        parent.installEventFilter(ToolbarOwnerEventFilter(parent=self))
        QObject.connect(self.timer, SIGNAL("timeout()"), self.hide)
        
    def add_toolbar(self, toolbar):
        if toolbar not in self.toolbars:
            self.toolbars.append(toolbar)
            toolbar.action.triggered.connect(self.display)
            
    def replace_toolbars(self):
        for toolbar in self.toolbars:
            toolbar.replace()
        
    def display(self):
        for toolbar in self.toolbars:
            if self.mode_opacity:
                toolbar.setStyleSheet("opacity:1")
            toolbar.show()
        self.timer.stop()
        self.delay = self.max_delay
        self.timer.start(self.max_delay)
        
    def hide(self):
        if not self.delay:
            return
        if self.mode_opacity:
            self.delay = int(self.delay/20)*10 
        else:
            self.delay = 0
        if self.delay == 0:
            self.timer.stop()
            for toolbar in self.toolbars:
                toolbar.hide()
        else:
            opacity = 255*self.delay/self.max_delay
            for toolbar in self.toolbars:
                toolbar.setStyleSheet("opacity:%f" % opacity)
            self.timer.setInterval(self.delay)

    def eventFilter(self, obj, e):
        if e.type() == QEvent.HoverMove:
            if (not self.delay) or self.delay < 500:
                self.display()
        return False
        
class Toolbar(QObject):
    def __init__(self, text, tooltip, callback, x, y, *args, **kwargs):
        super(Toolbar, self).__init__(*args, **kwargs)
        
        parent = self.parent()
        
        self.enabled = False
        self.x = x
        self.y = y
        
        self.toolbar = QToolBar(parent)
        self.toolbar.setAllowedAreas(Qt.NoToolBarArea)
        parent.addToolBar(Qt.NoToolBarArea, self.toolbar)

        self.action = QAction(text, parent)
        self.action.setToolTip(tooltip)
        self.toolbar.addAction(self.action)
        
        button = self.toolbar.children()[-1]
        self.toolbar.setContentsMargins(0, 0, 0, 0)
        
        font = button.font()
        font.setPointSizeF(font.pointSizeF() * 3)
        button.setFont(font)

        palette = self.toolbar.palette()
        button.setStyleSheet(
            """
            QToolButton {
                border : none;
                border-radius : %(border_radius)s;
                background: transparent;
                color: %(background_hover)s;
            }
            QToolButton:hover {
                background: %(background_hover)s;
                color: %(foreground_hover)s;
            }
            """ %
            {
                'border_radius': int(button.height()/2),
                'background_hover': palette.color(palette.Highlight).name(),
                'foreground_hover': palette.color(palette.HighlightedText).name(),
            }
        )
        self.toolbar.setStyleSheet("border:none;background:transparent")
        
        self.toolbar.resize(button.sizeHint())

        self.move(x, y)
        self.toolbar.setMovable(False)
        
        self.toolbar.hide()
        
        if callback:
            self.action.triggered.connect(callback)

    def replace(self):
        self.move(self.x, self.y)

    def move(self, x, y):
        """
        Move the toolbar to coordinates x,y
        If a coordinate is 0 < ? <= 1, it's a percent
        of the width or height
        """
        w_width = self.parent().width()
        t_width = self.toolbar.width()
        if not x or x < 0:
            _x = 0
        elif x > 1:
            _x = x
        else:
            _x = int(x * (w_width - t_width))
        if _x < 2:
            _x = 2
        elif _x > (w_width - t_width -2):
            _x = (w_width - t_width -2)

        w_height = self.parent().height()
        t_height = self.toolbar.height()
        if not y or y < 0:
            _y = 0
        elif y > 1:
            _y = y
        else:
            _y = int(y * (w_height - t_height))
        if _y < 2:
            _y = 2
        elif _y > (w_height - t_height -2):
            _y = (w_height - t_height -2)
            
        self.toolbar.move(_x, _y)
        
    def move_x(self, x):
        self.move(x, self.toolbar.y())
        
    def move_y(self, y):
        self.move(self.toolbar.x(), y)
        
    def disable(self):
        self.enabled = False
        
    def enable(self):
        self.enabled = True
        
    def hide(self):
        self.toolbar.hide()
        
    def show(self):
        if not self.enabled:
            return
        #self.toolbar.setStyleSheet("opacity:1")
        self.toolbar.show()
