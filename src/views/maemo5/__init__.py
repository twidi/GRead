# -*- coding: utf-8 -*-

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from PyQt4.QtMaemo5 import QMaemo5InformationBox

from ..mobile import ViewEventFilter as MobileViewEventFilter,  \
                     View            as MobileView

from .ui import Ui_Window # to load base_ui_window_class
                    
from engine import settings

class ViewEventFilter(MobileViewEventFilter):
    def preEventFilter(self, obj, event):
        if super(ViewEventFilter, self).preEventFilter(obj, event):
            return True
        if event.type() == QEvent.KeyPress:
            key = event.key()
            if key == Qt.Key_O and self.isShift(event):
                self.emit(SIGNAL("toggle_orientation"), True)
                return True
        return False

class View(MobileView):
    def __init__(self, *args,  **kwargs):
        super(View, self).__init__(*args, **kwargs)
        
        # for "back" button in title bar
        self.win.setAttribute(Qt.WA_Maemo5StackedWindow, True)
        
        # can handle landscape or portrait mode
        self.manage_orientation()
        
    def get_menu_container(self):
        return self.ui.menuBar
        
    def init_menu(self):
        self.add_orientation_menu()
        super(View, self).init_menu()
        
    def post_init_menu(self):
        self.context_menu_add_orientation()
        
    def manage_orientation(self):
        if self.controller.portrait_mode:
            if not self.win.testAttribute(Qt.WA_Maemo5PortraitOrientation):
                self.win.setAttribute(Qt.WA_Maemo5PortraitOrientation, True)
        else:
            if not self.win.testAttribute(Qt.WA_Maemo5LandscapeOrientation):
                self.win.setAttribute(Qt.WA_Maemo5LandscapeOrientation, True)

        # check the correct button
        if self.controller.is_current_view(self):
            if self.controller.portrait_mode:
                try:
                    self.action_orientation_portrait.setChecked(True)
                except:
                    pass
            else:
                try:
                    self.action_orientation_landscape.setChecked(True)
                except:
                    pass

    def add_orientation_menu(self):
        self.group_orientation = QActionGroup(self.win)
        self.action_orientation_landscape = QAction("Landscape", self.group_orientation)
        self.action_orientation_landscape.setCheckable(True)
        self.action_orientation_portrait = QAction("Portrait", self.group_orientation)
        self.action_orientation_portrait.setCheckable(True)
        self.get_menu_container().addActions(self.group_orientation.actions())
        self.action_orientation_portrait.toggled.connect(self.trigger_portrait_orientation)
            
    def toggle_orientation(self):
        self.action_orientation_portrait.setChecked(not self.action_orientation_portrait.isChecked())

    def trigger_portrait_orientation(self, checked):
        self.controller.set_portrait_mode(checked)
      
    def context_menu_add_orientation(self):
        """
        Add the orientation menus to the context menu
        """
        self.context_menu.addSeparator()
        self.context_menu.addActions(self.group_orientation.actions())
            
    def get_max_title_length(self):
        if self.controller.portrait_mode:
            return 11
        return 25

    def set_focused(self):
        super(View, self).set_focused()
        self.manage_orientation()

    def start_loading(self):
        self.win.setAttribute(Qt.WA_Maemo5ShowProgressIndicator, True)
            
    def stop_loading(self):
        self.win.setAttribute(Qt.WA_Maemo5ShowProgressIndicator, False)

    def add_event_filter(self, *args, **kwargs):
        super(View, self).add_event_filter(*args, **kwargs)
        QObject.connect(self.event_filter, SIGNAL("toggle_orientation"), self.toggle_orientation)

    def display_message(self, message, level="information", timeout=None):
        if timeout is None:
            timeout = QMaemo5InformationBox.DefaultTimeout
        QMaemo5InformationBox.information(self.win, '<p>%s</p>' % message, timeout)

    def show(self, *args, **kwargs):
        self.manage_orientation()
        super(View, self).show(*args, **kwargs)

from .. import basic
basic.base_view_class = View
basic.base_eventfilter_class = ViewEventFilter
