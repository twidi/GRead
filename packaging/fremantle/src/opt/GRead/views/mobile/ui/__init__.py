# -*- coding: utf-8 -*-

from PyQt4.QtCore import SIGNAL
from ...basic import ui

RequestContextMenuSignal = SIGNAL("request_context_menu(QPoint&)")

class ListView(ui.base_listview_class):
    def __init__(self, *args, **kwargs):
        super(ListView, self).__init__(*args, **kwargs)

    def mouseReleaseEvent(self, e):
        if self.indexAt(e.pos()).row() >= 0:
            max_width = self.width()
            if self.verticalScrollBar().isVisible():
                max_width = max_width - self.verticalScrollBar().sizeHint().width()
            if max_width - e.x() <= 50:
                self.emit(RequestContextMenuSignal, e.pos())
                return
        return super(ListView, self).mouseReleaseEvent(e)

class Ui_Window(ui.Ui_Window):
    pass
    
ui.base_ui_window_class = Ui_Window
ui.base_listview_class  = ListView
