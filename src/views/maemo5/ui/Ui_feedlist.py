# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/twidi/Projets/gread/src/views/maemo5/ui/feedlist.ui'
#
# Created: Tue Sep 14 04:04:11 2010
#      by: PyQt4 UI code generator 4.7.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_winFeedList(object):
    def setupUi(self, winFeedList):
        winFeedList.setObjectName("winFeedList")
        winFeedList.resize(800, 480)
        self.centralWidget = QtGui.QWidget(winFeedList)
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
        self.listFeedList = QtGui.QListView(self.centralWidget)
        self.listFeedList.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.listFeedList.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.listFeedList.setProperty("showDropIndicator", False)
        self.listFeedList.setUniformItemSizes(True)
        self.listFeedList.setWordWrap(True)
        self.listFeedList.setObjectName("listFeedList")
        self.verticalLayout.addWidget(self.listFeedList)
        winFeedList.setCentralWidget(self.centralWidget)
        self.menuBar = QtGui.QMenuBar(winFeedList)
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 800, 37))
        self.menuBar.setObjectName("menuBar")
        winFeedList.setMenuBar(self.menuBar)

        self.retranslateUi(winFeedList)
        QtCore.QMetaObject.connectSlotsByName(winFeedList)

    def retranslateUi(self, winFeedList):
        winFeedList.setWindowTitle(QtGui.QApplication.translate("winFeedList", "MainWindow", None, QtGui.QApplication.UnicodeUTF8))
        self.messageBox.setText(QtGui.QApplication.translate("winFeedList", "TextLabel", None, QtGui.QApplication.UnicodeUTF8))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    winFeedList = QtGui.QMainWindow()
    ui = Ui_winFeedList()
    ui.setupUi(winFeedList)
    winFeedList.show()
    sys.exit(app.exec_())

