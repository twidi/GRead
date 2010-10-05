# -*- coding: utf-8 -*-

"""
Item content view
"""
from ..mobile.itemview import ItemViewView as MobileItemViewView

ZOOMKEYS_ACTIVATED = False
try:
    from utils.zoomkeys import grab as grab_zoom_keys
    ZOOMKEYS_ACTIVATED = True
except Exception, e:
    import sys
    sys.stderr.write("ZOOMKEYS ERROR : %s\n" % e)

class ItemViewView(MobileItemViewView):
    
    def __init__(self, *args, **kwargs):
        super(ItemViewView, self).__init__(*args, **kwargs)
            
        # allow zoomkeys to be used to zoom
        if ZOOMKEYS_ACTIVATED:
            try:
                grab_zoom_keys(self.win.winId(), True)
            except Exception, e:
                pass
