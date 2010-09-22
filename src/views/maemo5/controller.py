# -*- coding: utf-8 -*-

"""
GRead controller
"""
from PyQt4.QtCore import QObject, Qt, QTimer, SIGNAL
from PyQt4.QtGui import QApplication

from ..basic.controller import Controller as BasicController

from feedlist import FeedListView
from itemlist import ItemListView
from itemview import ItemViewView
from settings_dialog import SettingsDialog

from engine import settings

class Controller(BasicController):
    
    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(*args, **kwargs)

        # manage orientation
        self.portrait_mode = False
        self.set_portrait_mode(settings.get('other', 'portrait_mode'))

        # manage scrolling titles
        self.title_timer = QTimer()
        QObject.connect(self.title_timer, SIGNAL("timeout()"), self.timeout_title_timer)
        
    def create_views(self):
        """
        Create all the views used by the application
        """
        self.settings_dialog = SettingsDialog(controller=self)
        self.feedlist_view   = FeedListView(controller=self)
        self.itemlist_view   = ItemListView(controller=self)
        self.itemview_view   = ItemViewView(controller=self)

    def settings_updated(self, *args, **kwargs):
        self.set_portrait_mode(settings.get('other', 'portrait_mode'))
        super(Controller, self).settings_updated(*args, **kwargs)

    def manage_orientation(self):
        """
        Manage the application orientation mode
        """
        for view in self.views:
            try:
                view.manage_orientation()
            except:
                pass

    def set_portrait_mode(self, portrait_mode):
        if portrait_mode == self.portrait_mode:
            return
        self.portrait_mode = portrait_mode
        self.manage_orientation()
        
    def get_title_operations_part(self):
        """
        Get the part of the title which will handle the running operations counter
        """
        nb = self.account.operations_manager.count_running()
        if nb:
            return "%d" % nb
        else:
            return ""
