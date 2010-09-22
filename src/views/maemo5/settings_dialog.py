# -*- coding: utf-8 -*-

"""
Settings view
"""
from PyQt4.QtGui import *
from PyQt4.QtCore import *

from ui.Ui_settings import Ui_Settings
from ..basic.settings_dialog import SettingsDialog as BasicSettingsDialog
from engine import settings

class SettingsDialog(BasicSettingsDialog):
    def get_ui_class(self):
        return Ui_Settings
    
    def update_inputs(self):
        super(SettingsDialog, self).update_inputs()
        
        self.ui.checkSettingsPortraitMode.setChecked(settings.get('other', 'portrait_mode'))
        self.ui.checkSettingsScrollTitles.setChecked(settings.get('other', 'scroll_titles'))
        
    def read_inputs(self):
        super(SettingsDialog, self).read_inputs()
        
        settings.set('other', 'portrait_mode', self.ui.checkSettingsPortraitMode.isChecked())
        settings.set('other', 'scroll_titles', self.ui.checkSettingsScrollTitles.isChecked())
