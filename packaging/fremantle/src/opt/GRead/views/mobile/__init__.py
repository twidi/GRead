# -*- coding: utf-8 -*-

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from ..basic import ViewEventFilter as BasicViewEventFilter,  \
                    View            as BasicView

from .ui import Ui_Window # to load base_ui_window_class
                    
from engine import settings

class ViewEventFilter(BasicViewEventFilter):
    pass
    
class View(BasicView):
        
    def update_title(self):
        if self.controller.current_view == self:
            self.controller.title_timer.stop()

        self.title = self.get_title()
        if not self.title:
            self.title = QApplication.applicationName()
        operations_part = self.controller.get_title_operations_part()
        if operations_part:
            self.title = "%s | %s" % (operations_part, self.title)
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
        return 25


from .. import basic
basic.base_view_class = View
basic.base_eventfilter_class = ViewEventFilter
