# -*- coding: utf-8 -*-

"""
Feeds Filter dialog
"""
from PyQt4.QtGui import *
from PyQt4.QtCore import *
    
from . import Dialog
from ui.Ui_filter_feeds import Ui_FilterFeeds
from . import ListModel

class FeedListModel(ListModel):        
    def data(self, index, role):
        if index.isValid() and role == Qt.DisplayRole:
            return QVariant(self.listdata[index.row()].title)
        else:
            return QVariant()
            
class EditEventFilter(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            key = event.key()
            if key == Qt.Key_Up:
                self.emit(SIGNAL("move_up"))
                return False
            elif key == Qt.Key_Down:
                self.emit(SIGNAL("move_down"))
                return False
        return QObject.eventFilter(self, obj, event)
            

class FilterFeedsDialog(Dialog):
    def __init__(self, *args, **kwargs):
        super(FilterFeedsDialog, self).__init__(*args, **kwargs)
        self.selected_feed = None
    
    def get_ui_class(self):
        return Ui_FilterFeeds

    def get_title(self):
        return "%s - Feed search" % QApplication.applicationName()
        
    def create(self):
        super(FilterFeedsDialog, self).create()
        flm = FeedListModel(data=[], view=self)
        
        self.proxy_model = QSortFilterProxyModel(self.win)
        self.proxy_model.setSourceModel(flm)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        
        self.ui.listFilter.setModel(self.proxy_model)
        self.ui.listFilter.activated.connect(self.activate_index)

        self.event_filter = EditEventFilter(self.ui.editFilter)
        self.ui.editFilter.installEventFilter(self.event_filter)
        QObject.connect(self.event_filter, SIGNAL("move_up"), self.move_up)
        QObject.connect(self.event_filter, SIGNAL("move_down"), self.move_down)
        self.ui.editFilter.textChanged.connect(self.filter_changed)
        self.ui.editFilter.returnPressed.connect(self.activate_current)
        
    def before_open(self):
        super(FilterFeedsDialog, self).before_open()
        feeds = self.controller.account.get_feeds(unread_only=self.controller.feedlist_view.unread_only)
        old_model = self.proxy_model.sourceModel()
        model = FeedListModel(data=feeds, view=self)
        self.proxy_model.setSourceModel(model)
        del old_model
        
        self.selected_feed = None
        
        try:
            model = self.ui.listFilter.model()
            self.ui.listFilter.setCurrentIndex(model.index(0, 0))
        except:
            pass

        self.ui.editFilter.setText('')
        self.ui.editFilter.setFocus(Qt.OtherFocusReason)

    def activate_index(self, index):
        self.selected_feed = self.get_selected()
        self.win.close()
        
    def get_selected(self):
        try:
            index = self.ui.listFilter.selectedIndexes()[0]
        except:
            return None
        else:
            source_index = self.proxy_model.mapToSource(index)
            return index.model().sourceModel().listdata[source_index.row()]
        
    def after_close(self):
        super(FilterFeedsDialog, self).after_close()
        if self.selected_feed:
            self.controller.feedlist_view.activate_entry(self.selected_feed, redraw=True)
            
    def filter_changed(self, text):
        self.proxy_model.setFilterWildcard(text)
        try:
            index = self.ui.listFilter.selectedIndexes()[0]
        except:
            try:
                model = self.ui.listFilter.model()
                self.ui.listFilter.setCurrentIndex(model.index(0, 0))
            except:
                pass
            
    def move_up(self):
        model = index = self.ui.listFilter.model()
        try:
            index = self.ui.listFilter.selectedIndexes()[0]
            row = index.row() - 1
            if row < 0:
                row = model.rowCount()-1
        except:
            row = 0
        try:
            self.ui.listFilter.setCurrentIndex(model.index(row, 0))
        except:
            pass
        
    def move_down(self):
        model = index = self.ui.listFilter.model()
        try:
            index = self.ui.listFilter.selectedIndexes()[0]
            row = index.row() + 1
            if row >= model.rowCount():
                row = 0
        except:
            row = 1
        try:
            self.ui.listFilter.setCurrentIndex(model.index(row, 0))
        except:
            pass
        
    def activate_current(self):
        try:
            index = self.ui.listFilter.selectedIndexes()[0]
        except:
            return
        else:
            self.activate_index(index)
        
