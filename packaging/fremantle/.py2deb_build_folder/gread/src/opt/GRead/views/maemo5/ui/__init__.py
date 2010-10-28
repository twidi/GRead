# -*- coding: utf-8 -*-

from PyQt4 import QtGui

from ...mobile.ui import Ui_Window as Mobile_Ui_Window

class Ui_Window(Mobile_Ui_Window): 

    def add_menu_container(self):
        self.menuBar = QtGui.QMenuBar(self.win)
        self.win.setMenuBar(self.menuBar)
    
from ...basic import ui
ui.base_ui_window_class = Ui_Window
