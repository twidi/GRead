# -*- coding: utf-8 -*-

"""
Feed list view
"""
from PyQt4.QtGui import *
from PyQt4.QtCore import *

from ..basic.feedlist import FeedListDelegate as BasicFeedListDelegate,  \
                             FeedListView     as BasicFeedListView

class FeedListDelegate(BasicFeedListDelegate):
    
    def sizeHint(self, *args, **kwargs):
        """
        Maemo5 optimization : all rows are 70 pixel height
        """
        size = QStyledItemDelegate.sizeHint(self, *args, **kwargs)
        if size.height() != 70:
            size.setHeight(70)
        return size
        
class FeedListView(BasicFeedListView):

    def get_feedlist_delegate_class(self):
        return FeedListDelegate

