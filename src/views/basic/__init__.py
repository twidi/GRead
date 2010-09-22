# -*- coding: utf-8 -*-

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from engine import settings

class ListModel(QAbstractListModel):
    def __init__(self, data, view):
        QAbstractListModel.__init__(self, view.win)
        self.view = view
        self.listdata   = data
        
    def rowCount(self, parent=QModelIndex()):
        return len(self.listdata)
        
    def row_of(self, item, start=0):
        row = None
        try:
            row = self.listdata.index(item)
        except:
            i = start
            for data in self.listdata[i:]:
                if data.id == item.id:
                    row = i
                    break
                i += 1
        return row
        
    def index_of(self, item, start=0):
        row = self.row_of(item, start)
        if row is not None:
            return self.index(row)
        return None
        
    def get_previous(self, item=None):
        if item is None:
            return None
        row = self.row_of(item)
        if row is None or row <= 0:
            return None
        try:
            return self.listdata[row-1]
        except:
            return None
        
    def get_next(self, item=None):
        if item is None:
            row = 0
        else:
            row = self.row_of(item)
            if row is None or row >= len(self.listdata)-1:
                return None
        try:
            return self.listdata[row + 1]
        except:
            return None

    #def removeRows(self, row, count, parent=QModelIndex()):
    #    self.beginRemoveRows(parent, row, row + count - 1)
    #    self.listdata = self.listdata[:row] + self.listdata[row+count:]
    #    self.endRemoveRows()

class WindowEventFilter(QObject):
    def __init__(self, parent=None):
        QObject.__init__(self, parent)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.ActivationChange:
            if self.parent().isActiveWindow():
                self.parent().view.set_focused()
        elif event.type() in (QEvent.KeyPress, QEvent.ShortcutOverride) \
            and event.key() in (Qt.Key_Backspace, Qt.Key_Escape):
            if self.parent().parent():
                self.parent().hide()
                return True

        return QObject.eventFilter(self, obj, event)
        
class ViewEventFilter(QObject):
    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        
    def isShift(self, event):
        return event.modifiers() & Qt.ShiftModifier

    def eventFilter(self, obj, event):
        return False

class View(object):
    def __init__(self, controller, ui, parent=None):
        """
        Initialize window
        """
        self.controller = controller
        self.controller.add_view(self)
        
        self.launched = False
        
        self.win = QMainWindow(parent, Qt.Window)

        self.win.view = self
        self.ui = ui()
        self.ui.setupUi(self.win)
        self.win.setWindowTitle(QApplication.applicationName())
        
        self.win.installEventFilter(WindowEventFilter(self.win))

        try:
            self.message_box_timer = QTimer()
            self.message_box_timer_running = False
            QObject.connect(self.message_box_timer, SIGNAL("timeout()"), self.timeout_message_box_timer)
        except:
            self.message_box_timer = None
        
        self.init_menu()
        self.post_init_menu()
        self.init_events()
        
    def init_menu(self):
        self.context_menu        = None
        self.context_menu_widget = None
        
    def post_init_menu(self):
        pass
        
    def init_events(self):
        pass
        
    def add_event_filter(self, widget, event_filter_class):
        self.event_filter = event_filter_class(self.win)
        widget.installEventFilter(self.event_filter)
        
    def display_message_box(self, text):
        try:
            self.message_box_timer.stop()
            self.ui.messageBox.setText(text)
            height = self.ui.messageBox.sizeHint().height()
            self.ui.messageBox.setMaximumHeight(height)
            self.ui.messageBox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            self.message_box_timer.start(500 + 100 * int(len(text)/50))
        except:
            self.display_message(text)
        
    def timeout_message_box_timer(self):
        if self.message_box_timer_running:
            return
        self.message_box_timer_running = True
        self.message_box_timer.setInterval(int(self.message_box_timer.interval()/1.2))
        height = self.ui.messageBox.height()
        if height == 0:
            self.message_box_timer.stop()
        else:
            self.ui.messageBox.setMaximumHeight(height-1)
        self.message_box_timer_running = False
        
    def show(self, app_just_launched=False):
        self.win.show()
        self.launched = True
        self.update_title()
        
    def make_context_menu(self, widget):
        """
        Create a context menu for the widget (the main widget for this view)
        """
        self.context_menu_widget = widget
        self.context_menu_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.context_menu_widget.customContextMenuRequested.connect(self.request_context_menu)
        self.context_menu = QMenu()
        
    def request_context_menu(self, pos):
        """
        Called when the user ask for the context menu to be displayed
        """
        pass
        
    def display_context_menu(self, pos):
        self.context_menu.exec_(self.context_menu_widget.mapToGlobal(pos))

    def settings_updated(self):
        pass

    def get_title(self):
        return QApplication.applicationName()
        
    def update_title(self):
        self.title = self.get_title()
        if not self.title:
            self.title = QApplication.applicationName()
        operations_part = self.controller.get_title_operations_part()
        if operations_part:
            self.title = "%s - %s" % (self.title, operations_part)
        self.win.setWindowTitle(self.title)
        
    def set_focused(self):
        self.controller.set_current_view(self)

    def start_loading(self):
        pass
            
    def stop_loading(self):
        pass

    def display_message(self, message, level="information"):
        """
        Display a message for a level ([information|warning|critical])
        """
        box = QMessageBox(self.win)
        box.setText(message)
        box.setWindowTitle(QApplication.applicationName())
        if level == "critical":
            box.setIcon(QMessageBox.Critical)
        elif level == "warning":
            box.setIcon(QMessageBox.Warning)
        else:
            box.setIcon(QMessageBox.Information)
        box.exec_()

base_view_class = View
base_eventfilter_class = ViewEventFilter
