# -*- coding: utf-8 -*-

from ...basic.ui import Ui_Window as Basic_Ui_Window

class Ui_Window(Basic_Ui_Window): 
    pass
    
from ...basic import ui
ui.base_ui_window_class = Ui_Window
