# -*- coding: utf-8 -*-

"""
Class for switching between scroll and selection in a QWebView
Ported from C++ from http://doc.qt.nokia.com/qt-maemo-4.6/maemo5-webview-qwebviewselectionsuppressor-h.html
(part of http://doc.qt.nokia.com/qt-maemo-4.6/maemo5-webview.html)
"""

from PyQt4.QtCore import QObject, Qt, QEvent

class QWebViewSelectionSuppressor(QObject):
    
    def __init__(self, view,  *args,  **kwargs):
        super(QWebViewSelectionSuppressor, self).__init__(*args, **kwargs)
        
        self.enabled = False
        self.mousePressed = False
        self.view = view
        
        self.enable()
        
    def enable(self):
        if self.enabled:
            return
        self.view.installEventFilter(self)
        self.enabled = True
        
    def disable(self):
        if not self.enabled:
            return
        self.view.removeEventFilter(self)
        self.enabled = False
        
    def isEnabled(self):
        return self.enabled
        
    def eventFilter(self, object, e):
        if e.type() == QEvent.MouseButtonPress:
            if e.button() == Qt.LeftButton:
                self.mousePressed = True
        elif e.type() == QEvent.MouseButtonRelease:
            if e.button() == Qt.LeftButton:
                self.mousePressed = False
        elif e.type() == QEvent.MouseMove:
            if self.mousePressed:
                return True
        return False
