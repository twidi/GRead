# -*- coding: utf-8 -*-

"""
Item list view
"""
from PyQt4.QtGui import *
from PyQt4.QtCore import *

from ..basic.itemlist import ItemListView as BasicItemListView
from ..mobile.ui import SwipeToRightSignal, SwipeToLeftSignal

class ItemListView(BasicItemListView):
    def __init__(self, *args, **kwargs):
        super(ItemListView, self).__init__(*args, **kwargs)
        QObject.connect(self.ui.listItemList, SwipeToRightSignal, self.mark_item_as_read)
        QObject.connect(self.ui.listItemList, SwipeToLeftSignal, self.mark_item_as_unread)

    def mark_item_as_read(self):
        self.get_selected()
        self.trigger_item_read(True)

    def mark_item_as_unread(self):
        self.get_selected()
        self.trigger_item_read(False)
