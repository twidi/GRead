# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
from . import base_ui_window_class, base_listview_class

class Ui_winItemList(base_ui_window_class):
        
    def init_geometry(self):
        self.win.resize(480, int(QtGui.QApplication.desktop().availableGeometry().height() / 20*9))
        self.win.move(0, int(QtGui.QApplication.desktop().availableGeometry().height() / 2))

    def add_widgets(self):
        self.listItemList = base_listview_class(self.centralWidget)
        self.listItemList.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.listItemList.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.listItemList.setProperty("showDropIndicator", False)
        self.listItemList.setUniformItemSizes(True)
        self.listItemList.setWordWrap(True)
        self.verticalLayout.addWidget(self.listItemList)
