# -*- coding: utf-8 -*-

"""
GRead controller for mobile
"""
from PyQt4.QtCore import QObject, Qt, QTimer, SIGNAL
from PyQt4.QtGui import QApplication

from ..basic.controller import Controller as BasicController

from itemview import ItemViewView
from settings_dialog import SettingsDialog

from engine import settings

class Controller(BasicController):
    
    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(*args, **kwargs)

        # manage scrolling titles
        self.title_timer = QTimer()
        QObject.connect(self.title_timer, SIGNAL("timeout()"), self.timeout_title_timer)
        
    def create_settings_dialog(self):
        self.settings_dialog = SettingsDialog(controller=self)
        
    def create_itemview_view(self):
        self.itemview_view = ItemViewView(controller=self)
        
    def get_title_operations_part(self):
        """
        Get the part of the title which will handle the running operations counter
        """
        nb = self.account.operations_manager.count_running()
        if nb:
            return "%d" % nb
        else:
            return ""
            
    def display_feed(self, feed):
        if self.current_view == self.itemview_view:
            self.itemview_view.win.hide()
        super(Controller, self).display_feed(feed)
            
    def timeout_title_timer(self):
        """
        Called when the title timer delay is done
        """
        if self.current_view:
            self.current_view.update_display_title()
