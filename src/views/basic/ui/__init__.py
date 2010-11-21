# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui


class Ui_Window(object):        
    def add_main_container(self):
        self.centralWidget = QtGui.QWidget(self.win)
        self.verticalLayout = QtGui.QVBoxLayout(self.centralWidget)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setMargin(0)
        self.win.setCentralWidget(self.centralWidget)
        
    def add_banner_top(self):
        self.bannerTop = QtGui.QLabel(self.centralWidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.bannerTop.sizePolicy().hasHeightForWidth())
        self.bannerTop.setSizePolicy(sizePolicy)
        self.bannerTop.setMaximumSize(QtCore.QSize(16777215, 0))
        self.bannerTop.setText("")
        self.bannerTop.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignHCenter)
        self.bannerTop.setWordWrap(True)
        self.verticalLayout.addWidget(self.bannerTop)

    def add_banner_bottom(self):
        self.bannerBottom = QtGui.QLabel(self.centralWidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.bannerBottom.sizePolicy().hasHeightForWidth())
        self.bannerBottom.setSizePolicy(sizePolicy)
        self.bannerBottom.setMaximumSize(QtCore.QSize(16777215, 0))
        self.bannerBottom.setText("")
        self.bannerBottom.setAlignment(QtCore.Qt.AlignTop|QtCore.Qt.AlignHCenter)
        self.bannerBottom.setWordWrap(True)
        self.verticalLayout.addWidget(self.bannerBottom)

    def add_menu_container(self):
        self.toolBar = QtGui.QToolBar(self.win)
        self.win.addToolBar(QtCore.Qt.ToolBarArea(QtCore.Qt.TopToolBarArea), self.toolBar)

    def setupUi(self, win):
        self.win = win
        self.add_main_container()
        self.add_banner_top()
        self.add_widgets()
        self.add_banner_bottom()
        self.add_menu_container()
        self.init_geometry()
        
    def init_geometry(self):
        pass

base_ui_window_class = Ui_Window
base_listview_class  = QtGui.QListView
