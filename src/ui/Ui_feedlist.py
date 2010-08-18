# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/twidi/Projets/gread/ui/feedlist.ui'
#
# Created: Thu Aug 12 09:12:55 2010
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
        self.verticalLayout.setMargin(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.listFeedList = QtGui.QListView(self.centralWidget)
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


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    winFeedList = QtGui.QMainWindow()
    ui = Ui_winFeedList()
    ui.setupUi(winFeedList)
    winFeedList.show()
    sys.exit(app.exec_())

