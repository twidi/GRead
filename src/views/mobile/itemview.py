# -*- coding: utf-8 -*-

"""
Item content view
"""
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtWebKit import *

from utils.qwebviewselectionsuppressor import QWebViewSelectionSuppressor
from utils.toolbar import ToolbarManager
from ..basic.itemview import ItemViewView as BasicItemViewView, \
                             ItemViewEventFilter as BasicItemViewEventFilter

class ItemViewEventFilter(BasicItemViewEventFilter):
    def preEventFilter(self, obj, event):
        if super(ItemViewEventFilter, self).preEventFilter(obj, event):
            return True
        if event.type() == QEvent.KeyPress:
            key = event.key()
            if key in (Qt.Key_Down, Qt.Key_Up, Qt.Key_Left, Qt.Key_Right, Qt.Key_Space):
                self.emit(SIGNAL("init_browser_scrollbars"))
                return False
        return False

class ItemViewView(BasicItemViewView):
    
    def __init__(self, *args, **kwargs):
        super(ItemViewView, self).__init__(*args, **kwargs)

        # remove selection when clic/drag to enable finger scrolling
        self.suppressor = QWebViewSelectionSuppressor(self.ui.webView)
        self.suppressor.enable()
        try:
            scroller = self.ui.webView.property("kineticScroller").toPyObject()
            if scroller:
                scroller.setEnabled(True)
        except:
            pass
            
    def get_event_filter_class(self):
        return ItemViewEventFilter

    def init_events(self):
        super(ItemViewView, self).init_events()
        QObject.connect(self.event_filter, SIGNAL("init_browser_scrollbars"), self.init_browser_scrollbars)
        
    def get_toolbar_manager_class(self):
        return ToolbarManager

    def get_toolbars(self):
        toolbars = super(ItemViewView, self).get_toolbars()
        toolbar_class = self.get_toolbar_class()
        self.bottomToolbar = toolbar_class('+', 'Toolbar', self.bottom_toolbar_pressed, 0.5, 1, parent=self.win)
        self.bottomToolbar.enable()
        toolbars.append(self.bottomToolbar)
        return toolbars

    def bottom_toolbar_pressed(self):
        pos = self.bottomToolbar.toolbar.pos()
        self.request_context_menu(pos)

    def show_previous(self):
        self.toolbar_manager.move_cursor_away_of_toolbar()
        super(ItemViewView, self).show_previous()

    def show_next(self):
        self.toolbar_manager.move_cursor_away_of_toolbar()
        super(ItemViewView, self).show_next()
        
        
    def init_browser_scrollbars(self):
        """
        We need scrollbars to navigate with keyboard
        """
        frame = self.ui.webView.page().currentFrame()
        if frame.scrollBarPolicy(Qt.Vertical) != Qt.ScrollBarAsNeeded:
            frame.setScrollBarPolicy(Qt.Vertical, Qt.ScrollBarAsNeeded)

    def help_keys(self):
        help = super(ItemViewView, self).help_keys()
        new_help = { 'title': help['title'], 'keys': []}
        for key in help['keys']:
            if key[0].startswith('F7'):
                new_help['keys'].append(('Vol. keys', key[1]))
            else:
                new_help['keys'].append(key)
        return new_help
