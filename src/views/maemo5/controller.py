# -*- coding: utf-8 -*-

"""
GRead controller for maemo5
"""
from PyQt4.QtCore import QObject, Qt, SIGNAL
from PyQt4.QtGui import QApplication
from PyQt4.QtMaemo5 import QMaemo5InformationBox

from ..mobile.controller import Controller as MobileController

from feedlist import FeedListView
from itemlist import ItemListView
from itemview import ItemViewView
from settings_dialog import SettingsDialog

from engine import settings

class Controller(MobileController):
    
    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(*args, **kwargs)

        # manage orientation
        self.portrait_mode = False
        self.set_portrait_mode(settings.get('other', 'portrait_mode'))
        
    def create_settings_dialog(self):
        self.settings_dialog = SettingsDialog(controller=self)
        
    def create_feedlist_view(self):
        self.feedlist_view = FeedListView(controller=self)
        
    def create_itemlist_view(self):
        self.itemlist_view = ItemListView(controller=self)
        
    def create_itemview_view(self):
        self.itemview_view = ItemViewView(controller=self)

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
        
    def display_message(self, message, level="information", timeout=None):
        """
        Display a message for the current view
        """
        if self.current_view:
            self.current_view.display_message(message, level, timeout)

    def trigger_help(self):
        self.display_message(self.compose_help_message(), timeout=QMaemo5InformationBox.NoTimeout)
        
    def compose_help_message(self):
        help = [
            self.help_keys(),
            self.feedlist_view.help_keys(),
            self.itemlist_view.help_keys(),
            self.itemview_view.help_keys(),
        ]
        text = ""
        num_cat = 0
        nb_cols = 2
        width_key   = 12
        width_title = 34
        if self.portrait_mode:
            nb_cols = 1
            width_key   = 20
            width_title = 66
        for cat in help:
            num_cat += 1
            if num_cat > 1:
                text += "<div style='font-size:2px'><hr /></div>\n"
            nb_rows = int((len(cat['keys'])+(1*nb_cols-1))/ nb_cols)
            text += "<table width='100%%' style='font-size:14px'>\n<tr><th rowspan='%d' align='left'><i>%s:</i></th>" % (nb_rows, cat['title'])
            col = 0
            num_key = 0
            for key in cat['keys']:
                col += 1
                num_key += 1
                if col == 1 and num_key > 1:
                    text += "<tr>"
                text += "<td width='%d%%' align='right'><b>%s</b>&nbsp;:&nbsp;</td><td width='%d%%'>%s&nbsp;</td>" % (width_key, key[0], width_title, key[1])
                if col == nb_cols:
                    text += "</tr>\n"
                    col = 0
            if col != 0 and nb_cols == 2:
                text += "<td colspan='2'>&nbsp;</td></tr>\n"
            text += "</table>\n"
        return text

    def help_keys(self):
        help = super(Controller, self).help_keys()
        help['keys'].append(
            ('shift-O', 'Toggle orientation'), 
        )
        return help
