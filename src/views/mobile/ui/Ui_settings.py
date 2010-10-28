# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui

from ...basic.ui.Ui_settings import Ui_Settings as Basic_Ui_Settings

class Ui_Settings(Basic_Ui_Settings):

    def addWidgets(self, Settings):
        super(Ui_Settings, self).addWidgets(Settings)        
        groupOther_row_count = self.gridLayout_groupOther.rowCount()
        self.checkSettingsScrollTitles = QtGui.QCheckBox(self.groupOther)
        self.checkSettingsScrollTitles.setObjectName("checkSettingsScrollTitles")
        self.gridLayout_groupOther.addWidget(self.checkSettingsScrollTitles, groupOther_row_count, 0, 1, 2)

    def setTabOrder(self, Settings):
        super(Ui_Settings, self).setTabOrder(Settings)
        Settings.setTabOrder(self.spinSettingsZoomFactor, self.checkSettingsScrollTitles)
        Settings.setTabOrder(self.checkSettingsScrollTitles, self.spinSettingsItemsToFetch)

    def retranslateUi(self, Settings):
        super(Ui_Settings, self).retranslateUi(Settings)
        self.checkSettingsScrollTitles.setText(QtGui.QApplication.translate("Settings", "Scroll long titles", None, QtGui.QApplication.UnicodeUTF8))
