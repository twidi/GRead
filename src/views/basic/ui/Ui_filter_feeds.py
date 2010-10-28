# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui

class Ui_FilterFeeds(object):
    def setupUi(self, FilterFeeds):
        FilterFeeds.setObjectName("FilterFeeds")
        FilterFeeds.resize(480, 400)
        self.verticalLayout = QtGui.QVBoxLayout(FilterFeeds)
        self.verticalLayout.setObjectName("verticalLayout")
        self.listFilter = QtGui.QListView(FilterFeeds)
        self.listFilter.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.listFilter.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.listFilter.setProperty("showDropIndicator", False)
        self.listFilter.setUniformItemSizes(True)
        self.listFilter.setWordWrap(True)
        self.listFilter.setObjectName("listFilter")
        self.verticalLayout.addWidget(self.listFilter)
        self.editFilter = QtGui.QLineEdit(FilterFeeds)
        self.editFilter.setObjectName("editFilter")
        self.verticalLayout.addWidget(self.editFilter)
