# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
from . import base_ui_window_class

class Ui_winFeedList(base_ui_window_class):
        
    def init_geometry(self):
        self.win.resize(480, int(QtGui.QApplication.desktop().availableGeometry().height() / 20*9))
        self.win.move(0, 0)
    
    def add_widgets(self):
        self.listFeedList = QtGui.QListView(self.centralWidget)
        self.listFeedList.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.listFeedList.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.listFeedList.setProperty("showDropIndicator", False)
        self.listFeedList.setUniformItemSizes(True)
        self.listFeedList.setWordWrap(True)
        self.verticalLayout.addWidget(self.listFeedList)
