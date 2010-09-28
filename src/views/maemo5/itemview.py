# -*- coding: utf-8 -*-

"""
Item content view
"""
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtWebKit import *

from utils.qwebviewselectionsuppressor import QWebViewSelectionSuppressor
from utils.toolbar import ToolbarManager
from ui.Ui_itemview import Ui_winItemView
from ..basic.itemview import ItemViewView as BasicItemViewView, \
                             ItemViewEventFilter as BasicItemViewEventFilter

ZOOMKEYS_ACTIVATED = False
try:
    from utils.zoomkeys import grab as grab_zoom_keys
    ZOOMKEYS_ACTIVATED = True
except Exception, e:
    sys.stderr.write("ZOOMKEYS ERROR : %s" % e)

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

class WebPage(QWebPage):
    def __init__(self, *args, **kwargs):
        super(WebPage, self).__init__(*args, **kwargs)
        
    def userAgentForUrl(self, url):
        return "Mozilla/5.0 (iPhone; U; CPU like Mac OS X; en) AppleWebKit/420+ (KHTML, like Gecko) Version/3.0 Mobile/1A543a Safari/419.3"

class ItemViewView(BasicItemViewView):
    
    def __init__(self, *args, **kwargs):
        super(ItemViewView, self).__init__(*args, **kwargs)

        # remove selection when clic/drag to enable finger scrolling
        self.suppressor = QWebViewSelectionSuppressor(self.ui.webView)
        self.suppressor.enable()
        scroller = self.ui.webView.property("kineticScroller").toPyObject()
        if scroller:
            scroller.setEnabled(True)
            
        # allow zoomkeys to be used to zoom
        if ZOOMKEYS_ACTIVATED:
            try:
                grab_zoom_keys(self.win.winId(), True)
            except Exception, e:
                pass

    def get_ui_class(self):
        return Ui_winItemView
                
    def get_web_page(self):
        return WebPage(parent=self.ui.webView)
            
    def get_event_filter_class(self):
        return ItemViewEventFilter

    def init_events(self):
        super(ItemViewView, self).init_events()
        QObject.connect(self.event_filter, SIGNAL("init_browser_scrollbars"), self.init_browser_scrollbars)
        
    def get_toolbar_manager_class(self):
        return ToolbarManager

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
