# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui

from ...mobile.ui.Ui_settings import Ui_Settings as Mobile_Ui_Settings

class Ui_Settings(Mobile_Ui_Settings):
    
    def addWidgets(self, Settings):
        super(Ui_Settings, self).addWidgets(Settings)        
        Settings.resize(800, 480)
        self.formLayout_groupGoogle.setContentsMargins(-1, 25, -1, -1)
        self.verticalLayout_groupFeeds.setContentsMargins(-1, 25, -1, -1)
        self.gridLayout_groupSpecials.setContentsMargins(-1, 19, -1, -1)
        self.verticalLayout_groupItems.setContentsMargins(-1, 25, -1, -1)
        self.verticalLayout_groupContent.setContentsMargins(-1, 25, -1, -1)
        self.verticalLayout_groupFeeds.setContentsMargins(-1, 25, -1, -1)
        self.verticalLayout_groupBanner.setContentsMargins(-1, 25, -1, -1)
        groupOther_row_count = self.gridLayout_groupOther.rowCount()
        self.checkSettingsPortraitMode = QtGui.QCheckBox(self.groupOther)
        self.checkSettingsPortraitMode.setObjectName("checkSettingsPortraitMode")
        self.gridLayout_groupOther.addWidget(self.checkSettingsPortraitMode, groupOther_row_count, 0, 1, 2)

    def setTabOrder(self, Settings):
        super(Ui_Settings, self).setTabOrder(Settings)
        Settings.setTabOrder(self.spinSettingsZoomFactor, self.checkSettingsPortraitMode)
        Settings.setTabOrder(self.checkSettingsPortraitMode, self.checkSettingsScrollTitles)

    def retranslateUi(self, Settings):
        super(Ui_Settings, self).retranslateUi(Settings)
        self.checkSettingsPortraitMode.setText(QtGui.QApplication.translate("Settings", "Portrait mode by default", None, QtGui.QApplication.UnicodeUTF8))
