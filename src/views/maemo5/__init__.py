# -*- coding: utf-8 -*-

from PyQt4.QtGui import *
from PyQt4.QtCore import *

import time

from engine import settings

MAEMO5_PRESENT = False
MAEMO5_ZOOMKEYS = False
try:
    from PyQt4.QtMaemo5 import QMaemo5InformationBox
    MAEMO5_PRESENT = True
except:
    pass

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

class View(object):
    def __init__(self, controller, ui, parent=None):
        """
        Initialize window
        """
        self.controller = controller
        self.controller.add_view(self)
        
        self.launched = False
        
        self.win = QMainWindow(parent, Qt.Window)

        if MAEMO5_PRESENT:
            self.win.setAttribute(Qt.WA_Maemo5StackedWindow, True)

        self.win.view = self
        self.ui = ui()
        self.ui.setupUi(self.win)
        self.win.setWindowTitle(QApplication.applicationName())
        
        self.win.installEventFilter(WindowEventFilter(self.win))

        if MAEMO5_PRESENT:
            self.manage_orientation()

        try:
            self.message_box_timer = QTimer()
            self.message_box_timer_running = False
            QObject.connect(self.message_box_timer, SIGNAL("timeout()"), self.timeout_message_box_timer)
        except:
            self.message_box_timer = None
        
    def display_message_box(self, text):
        try:
            self.message_box_timer.stop()
            self.ui.messageBox.setText(text)
            height = self.ui.messageBox.sizeHint().height()
            self.ui.messageBox.setMaximumHeight(height)
            self.ui.messageBox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            self.message_box_timer.start(250 + 100 * int(len(text)/50))
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
        self.manage_orientation()
        self.win.show()
        self.launched = True
        self.update_title()
                
    def manage_orientation(self):
        if MAEMO5_PRESENT:
            if self.controller.portrait_mode:
                if not self.win.testAttribute(Qt.WA_Maemo5PortraitOrientation):
                    self.win.setAttribute(Qt.WA_Maemo5PortraitOrientation, True)
            else:
                if not self.win.testAttribute(Qt.WA_Maemo5LandscapeOrientation):
                    self.win.setAttribute(Qt.WA_Maemo5LandscapeOrientation, True)

            # check the correct button
            if self.controller.is_current_view(self):
                if self.controller.portrait_mode:
                    try:
                        self.action_orientation_portrait.setChecked(True)
                    except:
                        raise
                        pass
                else:
                    try:
                        self.action_orientation_landscape.setChecked(True)
                    except:
                        raise
                        pass

    def add_orientation_menu(self):
        if MAEMO5_PRESENT:
            self.group_orientation = QActionGroup(self.win)
            self.action_orientation_landscape = QAction("Landscape", self.group_orientation)
            self.action_orientation_landscape.setCheckable(True)
            self.action_orientation_portrait = QAction("Portrait", self.group_orientation)
            self.action_orientation_portrait.setCheckable(True)
            self.ui.menuBar.addActions(self.group_orientation.actions())
            self.action_orientation_landscape.toggled.connect(self.toggle_orientation)
            self.action_orientation_portrait.toggled.connect(self.toggle_orientation)

    def toggle_orientation(self, checked):
        portrait_mode = False
        if self.action_orientation_portrait.isChecked():
            portrait_mode = True
        self.controller.set_portrait_mode(portrait_mode)

    def settings_updated(self):
        pass

    def get_title(self):
        return QApplication.applicationName()
        
    def update_title(self):
        if MAEMO5_PRESENT and self.controller.current_view == self:
            self.controller.title_timer.stop()
        self.title = self.get_title()
        if not self.title:
            self.title = QApplication.applicationName()
        operations_part = self.controller.get_title_operations_part()
        if operations_part:
            if MAEMO5_PRESENT:
                self.title = "(%s) %s" % (operations_part, self.title)
            else:
                self.title = "%s - %s" % (self.title, operations_part)
        self.win.setWindowTitle(self.title)
        
        self.title_start = 0
        self.title_step  = 2
        if MAEMO5_PRESENT and self.controller.current_view == self and len(self.title) > self.get_max_title_length():
            self.controller.title_timer.start(200)
            
    def get_max_title_length(self):
        if self.controller.portrait_mode:
            return 11
        return 25
            
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
        
    def set_focused(self):
        self.controller.set_current_view(self)
        self.manage_orientation()

    def start_loading(self):
        if MAEMO5_PRESENT:
            self.win.setAttribute(Qt.WA_Maemo5ShowProgressIndicator, True)
            
    def stop_loading(self):
        if MAEMO5_PRESENT:
            self.win.setAttribute(Qt.WA_Maemo5ShowProgressIndicator, False)

    def display_message(self, message, level="information"):
        """
        Display a message for a level ([information|warning|critical]), and handle the
        Maemo5 special case
        """
        if MAEMO5_PRESENT:
            QMaemo5InformationBox.information(self.win, '<p>%s</p>' % message, QMaemo5InformationBox.DefaultTimeout)
        else:
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
