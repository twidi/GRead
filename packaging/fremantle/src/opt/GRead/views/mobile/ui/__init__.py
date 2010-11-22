# -*- coding: utf-8 -*-

from PyQt4.QtCore import SIGNAL, QPoint
from ...basic import ui

RequestContextMenuSignal = SIGNAL("request_context_menu(QPoint&)")
SwipeToRightSignal       = SIGNAL("swipe_to_right")
SwipeToLeftSignal        = SIGNAL("swipe_to_left")

class ListView(ui.base_listview_class):
    def __init__(self, *args, **kwargs):
        super(ListView, self).__init__(*args, **kwargs)
        self.clickRightPosStatus = {
            'pending': False,
            'index':   None,
        }
        self.swipeToRightStatus = {
            'pending':   False,
            'index':     None,
            'start_pos': QPoint(),
        }

    def isRightPos(self, pos, area=50, index=None):
        if index is None:
            index = self.indexAt(pos)
        if index.row() >= 0:
            max_width = self.width()
            if self.verticalScrollBar().isVisible():
                max_width = max_width - self.verticalScrollBar().sizeHint().width()
            if max_width - pos.x() <= area:
                return True
        return False

    def mousePressEvent(self, e):
        pos   = e.pos()
        index = self.indexAt(pos)

        if self.isRightPos(pos=pos, index=index):
            self.clickRightPosStatus['pending'] = True
            self.clickRightPosStatus['index']   = index
        else:
            self.swipeToRightStatus['pending']   = True
            self.swipeToRightStatus['index']     = index
            self.swipeToRightStatus['start_pos'] = pos

        return super(ListView, self).mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        pos   = e.pos()
        index = self.indexAt(pos)

        if self.clickRightPosStatus['pending']:
            self.clickRightPosStatus['pending'] = False
            if index == self.clickRightPosStatus['index'] and self.isRightPos(pos=pos, index=index):
                self.emit(RequestContextMenuSignal, pos)
                return
        elif self.swipeToRightStatus['pending']:
            self.swipeToRightStatus['pending'] = False
            if index == self.swipeToRightStatus['index'] and abs(self.swipeToRightStatus['start_pos'].x() - pos.x()) >= 80:
                if pos.x() > self.swipeToRightStatus['start_pos'].x():
                    self.emit(SwipeToRightSignal)
                else:
                    self.emit(SwipeToLeftSignal)
                return
        return super(ListView, self).mouseReleaseEvent(e)

class Ui_Window(ui.Ui_Window):
    pass
    
ui.base_ui_window_class = Ui_Window
ui.base_listview_class  = ListView
