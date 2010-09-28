# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/twidi/Projets/gread/src/views/basic/ui/filter_feeds.ui'
#
# Created: Tue Sep 28 16:41:58 2010
#      by: PyQt4 UI code generator 4.7.3
#
# WARNING! All changes made in this file will be lost!

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

        self.retranslateUi(FilterFeeds)
        QtCore.QMetaObject.connectSlotsByName(FilterFeeds)

    def retranslateUi(self, FilterFeeds):
        FilterFeeds.setWindowTitle(QtGui.QApplication.translate("FilterFeeds", "Dialog", None, QtGui.QApplication.UnicodeUTF8))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    FilterFeeds = QtGui.QDialog()
    ui = Ui_FilterFeeds()
    ui.setupUi(FilterFeeds)
    FilterFeeds.show()
    sys.exit(app.exec_())

