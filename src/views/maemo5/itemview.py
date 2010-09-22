# -*- coding: utf-8 -*-

"""
Item content view
"""
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtWebKit import *

from utils.qwebviewselectionsuppressor import QWebViewSelectionSuppressor
from utils.toolbar import ToolbarManager
from ..basic.itemview import ItemViewView as BasicItemViewView

ZOOMKEYS_ACTIVATED = False
try:
    from utils.zoomkeys import grab as grab_zoom_keys
    ZOOMKEYS_ACTIVATED = True
except Exception, e:
    sys.stderr.write("ZOOMKEYS ERROR : %s" % e)

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
        
    def get_toolbar_manager_class(self):
        return ToolbarManager

    def set_current_item(self, item):
        if not super(ItemViewView, self).set_current_item(item):
            return
            
        str = "%s - " % item.title
        statuses = []
        if item.unread:
            statuses.append('unread')
        else:
            statuses.append('read')
        if item.shared:
            statuses.append('shared')
        if item.starred:
            statuses.append('starred')
        self.display_message_box("%s [%s]" % (item.title, ', '.join(statuses)))

        return True
