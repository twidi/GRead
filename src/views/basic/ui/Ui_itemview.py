# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/twidi/Projets/gread/src/views/basic/ui/itemview.ui'
#
# Created: Tue Sep 28 16:43:17 2010
#      by: PyQt4 UI code generator 4.7.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_winItemView(object):
    def setupUi(self, winItemView):
        winItemView.setObjectName("winItemView")
        winItemView.resize(800, 480)
        self.centralWidget = QtGui.QWidget(winItemView)
        self.centralWidget.setObjectName("centralWidget")
        self.verticalLayout = QtGui.QVBoxLayout(self.centralWidget)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setMargin(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.bannerTop = QtGui.QLabel(self.centralWidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.bannerTop.sizePolicy().hasHeightForWidth())
        self.bannerTop.setSizePolicy(sizePolicy)
        self.bannerTop.setMaximumSize(QtCore.QSize(16777215, 0))
        self.bannerTop.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignHCenter)
        self.bannerTop.setWordWrap(True)
        self.bannerTop.setObjectName("bannerTop")
        self.verticalLayout.addWidget(self.bannerTop)
        self.webView = QtWebKit.QWebView(self.centralWidget)
        self.webView.setObjectName("webView")
        self.verticalLayout.addWidget(self.webView)
        self.bannerBottom = QtGui.QLabel(self.centralWidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.bannerBottom.sizePolicy().hasHeightForWidth())
        self.bannerBottom.setSizePolicy(sizePolicy)
        self.bannerBottom.setMaximumSize(QtCore.QSize(16777215, 0))
        self.bannerBottom.setAlignment(QtCore.Qt.AlignTop|QtCore.Qt.AlignHCenter)
        self.bannerBottom.setWordWrap(True)
        self.bannerBottom.setObjectName("bannerBottom")
        self.verticalLayout.addWidget(self.bannerBottom)
        winItemView.setCentralWidget(self.centralWidget)
        self.toolBar = QtGui.QToolBar(winItemView)
        self.toolBar.setObjectName("toolBar")
        winItemView.addToolBar(QtCore.Qt.ToolBarArea(QtCore.Qt.TopToolBarArea), self.toolBar)

        self.retranslateUi(winItemView)
        QtCore.QMetaObject.connectSlotsByName(winItemView)

    def retranslateUi(self, winItemView):
        winItemView.setWindowTitle(QtGui.QApplication.translate("winItemView", "MainWindow", None, QtGui.QApplication.UnicodeUTF8))
        self.bannerTop.setText(QtGui.QApplication.translate("winItemView", "TextLabel", None, QtGui.QApplication.UnicodeUTF8))
        self.bannerBottom.setText(QtGui.QApplication.translate("winItemView", "TextLabel", None, QtGui.QApplication.UnicodeUTF8))
        self.toolBar.setWindowTitle(QtGui.QApplication.translate("winItemView", "toolBar", None, QtGui.QApplication.UnicodeUTF8))

from PyQt4 import QtWebKit

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    winItemView = QtGui.QMainWindow()
    ui = Ui_winItemView()
    ui.setupUi(winItemView)
    winItemView.show()
    sys.exit(app.exec_())

