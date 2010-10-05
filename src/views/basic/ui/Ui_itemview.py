# -*- coding: utf-8 -*-

from PyQt4 import QtGui, QtWebKit
from . import base_ui_window_class

class Ui_winItemView(base_ui_window_class):
        
    def init_geometry(self):
        self.win.resize(QtGui.QApplication.desktop().availableGeometry().width() - 490, QtGui.QApplication.desktop().availableGeometry().height())
        self.win.move(490, 0)

    def add_widgets(self):
        self.webView = QtWebKit.QWebView(self.centralWidget)
        self.verticalLayout.addWidget(self.webView)
