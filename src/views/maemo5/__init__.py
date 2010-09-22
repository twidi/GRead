# -*- coding: utf-8 -*-

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from ..basic import ViewEventFilter as BasicViewEventFilter,  \
                    View            as BasicView
                    
from engine import settings

class ViewEventFilter(BasicViewEventFilter):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            key = event.key()
            if key == Qt.Key_O:
                self.emit(SIGNAL("toggle_orientation"), True)
                return True
        return False

class View(BasicView):
    def __init__(self, *args,  **kwargs):
        super(View, self).__init__(*args, **kwargs)
        
        # for "back" button in title bar
        self.win.setAttribute(Qt.WA_Maemo5StackedWindow, True)
        
        # can handle landscape or portrait mode
        self.manage_orientation()
        
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
        self.ui.menuBar.addActions(self.group_orientation.actions())
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
        
    def update_title(self):
        if self.controller.current_view == self:
            self.controller.title_timer.stop()

        self.title = self.get_title()
        if not self.title:
            self.title = QApplication.applicationName()
        operations_part = self.controller.get_title_operations_part()
        if operations_part:
            self.title = "(%s) %s" % (operations_part, self.title)
        self.win.setWindowTitle(self.title)
        
        self.title_start = 0
        self.title_step  = 2

        if self.controller.current_view == self and len(self.title) > self.get_max_title_length():
            self.controller.title_timer.start(200)
            
    def update_display_title(self):
        max = self.get_max_title_length()
        if not settings.get('other', 'scroll_titles') or len(self.title) <= max:
            display_title = self.title
            self.controller.title_timer.stop()
        else:
            self.title_start += self.title_step
            if self.title_start < 0 or len(self.title) - self.title_start < max:
                self.title_step = self.title_step * -1
                self.title_start += self.title_step
            display_title = self.title[self.title_start:]
        self.win.setWindowTitle(display_title)
            
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

    def display_message(self, message, level="information"):
        QMaemo5InformationBox.information(self.win, '<p>%s</p>' % message, QMaemo5InformationBox.DefaultTimeout)

    def show(self, *args, **kwargs):
        self.manage_orientation()
        super(View, self).show(*args, **kwargs)

from .. import basic
basic.base_view_class = View
basic.base_eventfilter_class = ViewEventFilter
