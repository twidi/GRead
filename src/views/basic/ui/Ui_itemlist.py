# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/twidi/Projets/gread/src/views/maemo5/ui/itemlist.ui'
#
# Created: Mon Sep 13 22:30:37 2010
#      by: PyQt4 UI code generator 4.7.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_winItemList(object):
    def setupUi(self, winItemList):
        winItemList.setObjectName("winItemList")
        winItemList.resize(800, 480)
        self.centralWidget = QtGui.QWidget(winItemList)
        self.centralWidget.setObjectName("centralWidget")
        self.verticalLayout = QtGui.QVBoxLayout(self.centralWidget)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setMargin(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.messageBox = QtGui.QLabel(self.centralWidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.messageBox.sizePolicy().hasHeightForWidth())
        self.messageBox.setSizePolicy(sizePolicy)
        self.messageBox.setMaximumSize(QtCore.QSize(16777215, 0))
        self.messageBox.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignHCenter)
        self.messageBox.setWordWrap(True)
        self.messageBox.setObjectName("messageBox")
        self.verticalLayout.addWidget(self.messageBox)
        self.listItemList = QtGui.QListView(self.centralWidget)
        self.listItemList.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.listItemList.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.listItemList.setProperty("showDropIndicator", False)
        self.listItemList.setUniformItemSizes(True)
        self.listItemList.setWordWrap(True)
        self.listItemList.setObjectName("listItemList")
        self.verticalLayout.addWidget(self.listItemList)
        winItemList.setCentralWidget(self.centralWidget)
        self.menuBar = QtGui.QMenuBar(winItemList)
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 800, 37))
        self.menuBar.setObjectName("menuBar")
        winItemList.setMenuBar(self.menuBar)

        self.retranslateUi(winItemList)
        QtCore.QMetaObject.connectSlotsByName(winItemList)

    def retranslateUi(self, winItemList):
        winItemList.setWindowTitle(QtGui.QApplication.translate("winItemList", "MainWindow", None, QtGui.QApplication.UnicodeUTF8))
        self.messageBox.setText(QtGui.QApplication.translate("winItemList", "TextLabel", None, QtGui.QApplication.UnicodeUTF8))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    winItemList = QtGui.QMainWindow()
    ui = Ui_winItemList()
    ui.setupUi(winItemList)
    winItemList.show()
    sys.exit(app.exec_())

