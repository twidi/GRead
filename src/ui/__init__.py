# -*- coding: utf-8 -*-

"""
Controller for ui
"""


from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtWebKit import *
    
from ui.Ui_feedlist import Ui_winFeedList
from ui.Ui_itemlist import Ui_winItemList
from ui.Ui_itemview import Ui_winItemView
from ui.Ui_settings import Ui_Settings

from utils.qwebviewselectionsuppressor import QWebViewSelectionSuppressor
from operation import Operation
import time

MAEMO5_PRESENT = False
MAEMO5_ZOOMKEYS = False
try:
    from PyQt4.QtMaemo5 import QMaemo5InformationBox
    MAEMO5_PRESENT = True
    try:
        from utils.zoomkeys import grab as grab_zoom_keys
        MAEMO5_ZOOMKEYS = True
    except:
        pass
except:
    pass

class FeedListDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        """
        Paint the list item with the default options, then add the unread counter
        """
        painter.save()

        try:
            is_category = False
            
            model = index.model()
            item = model.listdata[index.row()]

            styleOption = QStyleOptionViewItemV4(option)
            try:
                styleOption.text = item.title
                styleOption.rect.adjust(15, 0, 0, 0)
                if item.__class__.__name__ != 'Feed':
                    styleOption.font.setStyle(QFont.StyleItalic)
                if item.unread and not model.controller.show_updated:
                    styleOption.font.setWeight(QFont.Bold)
            except Exception, e:
                is_category = True
                styleOption.text = item.label
                styleOption.font.setWeight(QFont.Bold)
                if item.id == 'specials':
                    styleOption.font.setStyle(QFont.StyleItalic)

            self.parent().style().drawControl(QStyle.CE_ItemViewItem, styleOption, painter)
                        
            if item.unread:
                if is_category:
                    str_unread = "%d/%d" % (item.unread, len([feed for feed in item.getFeeds() if feed.unread]))
                else:
                    str_unread = "%d" % item.unread
                painter.drawText(option.rect, Qt.AlignRight | Qt.AlignVCenter, str_unread)

        finally:
            painter.restore()
    
class ListModel(QAbstractListModel):
    def __init__(self, data, controller):
        QAbstractListModel.__init__(self, controller.win)
        self.controller = controller
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
    
class FeedListModel(ListModel):        
    def data(self, index, role):
        if index.isValid() and role == Qt.DisplayRole:
            try:
                text = self.listdata[index.row()].title
            except:
                text = self.listdata[index.row()].label
            return QVariant(text)
        else:
            return QVariant()

class ItemListDelegate(QStyledItemDelegate):
    def sizeHint(self, option, index):
        size = super(ItemListDelegate, self).sizeHint(option, index)
        try:
            if index.model().listdata[index.row()].parent.__class__.__name__ != 'Feed':
                metrics = QFontMetrics(option.font)
                min_height = int(metrics.height() * 1.8) * 1.1
                if size.height() < min_height:
                    size.setHeight(min_height)
        except:
            pass
        return size

    def paint(self, painter, option, index):
        """
        Paint the list item with the default options, and bold unread items
        """
        painter.save()

        try:            
            model = index.model()
            item = model.listdata[index.row()]

            styleOption = QStyleOptionViewItemV4(option)
            styleOption.text = item.title
            if item.isUnread():
                styleOption.font.setWeight(QFont.Bold)

            if item.parent.__class__.__name__ != 'Feed':
                styleOption.displayAlignment = Qt.AlignTop | Qt.AlignLeft

            self.parent().style().drawControl(QStyle.CE_ItemViewItem, styleOption, painter)

            if item.parent.__class__.__name__ != 'Feed':
                text = ''
                if getattr(item.parent, 'type', '') == 'broadcast-friends':
                    friend = item.data['via'][0]['title'].rstrip("'s shared items")
                    try:
                        text = "by %s (%s)" % (friend, item.feed.title)
                    except:
                        text = "by %s" % friend
                elif getattr(item.parent, 'type', '') == 'created':
                    text = item.data['origin']['title']
                else:
                    try:
                        text = item.feed.title
                    except:
                        text = item.data['origin']['title']

                if text:
                    styleOption2 = QStyleOptionViewItemV4(option)
                    font = styleOption2.font
                    font.setPointSizeF(font.pointSizeF() * 0.8)
                    font.setStyle(QFont.StyleItalic)
                    font.setWeight(QFont.Normal)
                    painter.setFont(font)

                    rect = styleOption2.rect
                    rect.adjust(3, 0, 0, -int(rect.size().height()*0.1))
                    painter.drawText(rect, Qt.AlignBottom | Qt.AlignLeft, text)

        finally:
            painter.restore()
            
class ItemListModel(ListModel):
    def data(self, index, role):
        if index.isValid() and role == Qt.DisplayRole:
            return QVariant(self.listdata[index.row()].title)
        else:
            return QVariant()

class WindowEventFilter(QObject):
    def __init__(self, parent=None):
        QObject.__init__(self, parent)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.ActivationChange:
            if self.parent().isActiveWindow():
                self.parent().controller.set_focused()
        return QObject.eventFilter(self, obj, event)

class WindowController(object):
    def __init__(self, ui_controller, ui, parent=None):
        """
        Initialize window
        """
        self.ui_controller = ui_controller
        self.ui_controller.add_controller(self)
        self.gread = self.ui_controller.gread
        self.settings = self.gread.settings
        self.operation_manager = self.gread.operation_manager
        
        self.launched = False
        
        self.win = QMainWindow(parent, Qt.Window)

        if MAEMO5_PRESENT:
            self.win.setAttribute(Qt.WA_Maemo5StackedWindow, True)
            if self.gread.settings['other']['auto_rotation']:
                self.win.setAttribute(Qt.WA_Maemo5AutoOrientation, True)

        self.win.controller = self
        self.ui = ui()
        self.ui.setupUi(self.win)
        self.win.setWindowTitle(QApplication.applicationName())
        
        self.win.installEventFilter(WindowEventFilter(self.win))

        if MAEMO5_PRESENT:
            self.manage_orientation()
        
    def show(self, app_just_launched=False):
        if MAEMO5_PRESENT and self.gread.settings['other']['auto_rotation'] and self.ui_controller.portrait_mode:
            # bad hack to force new window to start in portrait mode if needed. removed by manage_orientation, called by set_focused
            self.win.setAttribute(Qt.WA_Maemo5PortraitOrientation, True)
            
        self.win.show()
        self.launched = True
        self.update_title()
                
    def manage_orientation(self):
        # bad hack to force new window to start in portrait mode if needed
        if MAEMO5_PRESENT and self.gread.settings['other']['auto_rotation']:
            size = self.win.size()
            if self.ui_controller.portrait_mode and size.height() < size.width():
                self.win.setAttribute(Qt.WA_Maemo5PortraitOrientation, True)
            if self.win.testAttribute(Qt.WA_Maemo5PortraitOrientation):
                time.sleep(2)
                self.win.setAttribute(Qt.WA_Maemo5AutoOrientation, True)
                self.win.setAttribute(Qt.WA_Maemo5PortraitOrientation, False)

    def settings_updated(self):
        if MAEMO5_PRESENT:
            self.win.setAttribute(Qt.WA_Maemo5AutoOrientation, self.settings['other']['auto_rotation'])

    def get_title(self):
        return QApplication.applicationName()
        
    def update_title(self):
        if MAEMO5_PRESENT and self.ui_controller.current == self:
            self.ui_controller.title_timer.stop()
        self.title = self.get_title()
        if not self.title:
            self.title = QApplication.applicationName()
        operations_part = self.ui_controller.get_title_operations_part()
        if operations_part:
            if MAEMO5_PRESENT:
                self.title = "(%s) %s" % (operations_part, self.title)
            else:
                self.title = "%s - %s" % (self.title, operations_part)
        self.win.setWindowTitle(self.title)
        
        self.title_start = 0
        self.title_step  = 2
        if MAEMO5_PRESENT and self.ui_controller.current == self and len(self.title) > self.get_max_title_length():
            self.ui_controller.title_timer.start(200)
            
    def get_max_title_length(self):
        if self.ui_controller.portrait_mode:
            return 11
        return 25
            
    def update_display_title(self):
        max = self.get_max_title_length()
        if len(self.title) <= max:
            display_title = self.title
            self.ui_controller.title_timer.stop()
        else:
            self.title_start += self.title_step
            if self.title_start < 0 or len(self.title) - self.title_start < max:
                self.title_step = self.title_step * -1
                self.title_start += self.title_step
            display_title = self.title[self.title_start:]
        self.win.setWindowTitle(display_title)
        
    def set_focused(self):
        self.ui_controller.set_current(self)
        self.manage_orientation()

    def start_loading(self):
        if MAEMO5_PRESENT:
            self.win.setAttribute(Qt.WA_Maemo5ShowProgressIndicator, True)
            
    def stop_loading(self):
        if MAEMO5_PRESENT:
            self.win.setAttribute(Qt.WA_Maemo5ShowProgressIndicator, False)

class FeedListController(WindowController):
    def __init__(self, ui_controller):
        super(FeedListController, self).__init__(ui_controller, Ui_winFeedList)
        
        self.current_category = None
        self.show_updated     = self.settings['feeds']['show_updated']

        self.selected_category = None
        self.selected_feed     = None
        
        # simple menu boutons
        self.action_settings = QAction("Settings", self.win)
        self.action_settings.setObjectName('actionSettings')
        self.action_sync = QAction("Synchronize", self.win)
        self.action_sync.setDisabled(not self.gread.auth_settings_ready())
        self.action_sync.setObjectName('actionSync')
        self.ui.menuBar.addAction(self.action_settings)
        self.ui.menuBar.addAction(self.action_sync)
        self.action_settings.triggered.connect(self.trigger_settings)
        self.action_sync.triggered.connect(self.trigger_sync)

        # menu boutons : group for show all/updated
        self.group_show = QActionGroup(self.win)
        self.action_show_all = QAction("Show all", self.group_show)
        self.action_show_all.setCheckable(True)
        self.action_show_all.setDisabled(True)
        self.action_show_updated = QAction("Show updated", self.group_show)
        self.action_show_updated.setCheckable(True)
        self.action_show_updated.setDisabled(True)
        if self.settings['feeds']['show_updated']:
            self.action_show_updated.setChecked(True)
        else:
            self.action_show_all.setChecked(True)
        self.ui.menuBar.addActions(self.group_show.actions())
        self.action_show_updated.toggled.connect(self.toggle_show_updated)
        
        # feed list
        flm = FeedListModel(data=[], controller=self)
        fld = FeedListDelegate(self.win)
        self.ui.listFeedList.setModel(flm)
        self.ui.listFeedList.setItemDelegate(fld)
        self.ui.listFeedList.activated.connect(self.activate_entry)
        
    def trigger_settings(self):
        """
        Display the settings dialog box and save settings on exit
        """
        self.ui.menuBar.setDisabled(True)
        
        # create dialog
        Settings = QDialog()
        ui = Ui_Settings()
        ui.setupUi(Settings)
        Settings.setWindowTitle("%s - Settings" % QApplication.applicationName())

        # fill inputs
        ui.inputSettingsAccount.setText( self.settings['google']['account'])
        ui.inputSettingsPassword.setText(self.settings['google']['password'])
        try:
            ui.selectSettingsHomeDefault.setCurrentIndex(self.gread.settings_helpers['feeds_default'].index(self.settings['feeds']['default']))
        except:
            ui.selectSettingsHomeDefault.setCurrentIndex(0)
        try:
            ui.selectSettingsHomeAllEntries.setCurrentIndex(self.gread.settings_helpers['feeds_all_entries'].index(self.settings['feeds']['all_entries']))
        except:
            ui.selectSettingsHomeAllEntries.setCurrentIndex(0)

        ui.checkSettingsHomeShowUpdated.setChecked(self.settings['feeds']['show_updated'])

        ui.checkSettingsShowShared.setChecked(    self.settings['feeds']['show_broadcast'])
        ui.checkSettingsShowStarred.setChecked(   self.settings['feeds']['show_starred'])
        ui.checkSettingsShowNotes.setChecked(     self.settings['feeds']['show_created'])
        ui.checkSettingsShowAll.setChecked(       self.settings['feeds']['show_reading-list'])
        ui.checkSettingsShowRead.setChecked(      self.settings['feeds']['show_read'])
        ui.checkSettingsShowFriends.setChecked(   self.settings['feeds']['show_broadcast-friends'])
        ui.checkSettingsShowKeptUnread.setChecked(self.settings['feeds']['show_kept-unread'])

        try:
            ui.selectSettingsItemsShowMode.setCurrentIndex(self.gread.settings_helpers['items_show_mode'].index(self.settings['items']['show_mode']))
        except:
            ui.selectSettingsItemsShowMode.setCurrentIndex(0)

        if MAEMO5_PRESENT:
            ui.checkSettingsAutoRotation.setChecked(self.settings['other']['auto_rotation'])
        else:
            ui.checkSettingsAutoRotation.hide()
            ui.groupOther.hide() # Remove when somehing else will be in other

        # display window
        Settings.exec_()
        
        # save new settings
        google_credentials_changed = False
        google_was_verified        = self.settings['google']['verified']
        google_account  = ui.inputSettingsAccount.text()
        google_password = ui.inputSettingsPassword.text()
        if self.settings['google']['account'] != google_account \
        or self.settings['google']['password'] != google_password:
            self.settings['google']['verified'] = False
            self.settings['google']['auth_token'] = ''
            self.settings['google']['token'] = ''
            google_credentials_changed = True
        self.settings['google']['account']  = google_account
        self.settings['google']['password'] = google_password

        try:
            self.settings['feeds']['default'] = self.gread.settings_helpers['feeds_default'][ui.selectSettingsHomeDefault.currentIndex()]
        except:
            pass
        try:
            self.settings['feeds']['all_entries'] = self.gread.settings_helpers['feeds_all_entries'][ui.selectSettingsHomeAllEntries.currentIndex()]
        except:
            pass

        self.settings['feeds']['show_updated']    = ui.checkSettingsHomeShowUpdated.isChecked()

        self.settings['feeds']['show_broadcast']         = ui.checkSettingsShowShared.isChecked()
        self.settings['feeds']['show_starred']           = ui.checkSettingsShowStarred.isChecked()
        self.settings['feeds']['show_created']           = ui.checkSettingsShowNotes.isChecked()
        self.settings['feeds']['show_reading-list']      = ui.checkSettingsShowAll.isChecked()
        self.settings['feeds']['show_read']              = ui.checkSettingsShowRead.isChecked()
        self.settings['feeds']['show_broadcast-friends'] = ui.checkSettingsShowFriends.isChecked()
        self.settings['feeds']['show_kept-unread']       = ui.checkSettingsShowKeptUnread.isChecked()

        try:
            self.settings['items']['show_mode'] = self.gread.settings_helpers['items_show_mode'][ui.selectSettingsItemsShowMode.currentIndex()]
        except:
            pass

        if MAEMO5_PRESENT:
            self.settings['other']['auto_rotation'] = ui.checkSettingsAutoRotation.isChecked()

        self.gread.save_settings()
        self.ui.menuBar.setDisabled(False)
                
        if not google_was_verified and google_credentials_changed and self.gread.auth_settings_ready():
            self.trigger_sync()
            
    def update_feed_list(self):
        """
        Empty and then refill the feed list with current options
        """
        if not self.gread.authenticated:
            return
        self.update_listview(content=self.gread.get_home_content(self.show_updated, self.current_category))
        # restore selection
        if self.selected_category:
            category_index = self.ui.listFeedList.model().index_of(self.selected_category)
            if category_index:
                self.ui.listFeedList.setCurrentIndex(category_index)
                if self.selected_feed:
                    feed_index = self.ui.listFeedList.model().index_of(self.selected_feed, start=category_index.row()+1)
                    if feed_index:
                        self.ui.listFeedList.setCurrentIndex(feed_index)

    def update_listview(self, content=[]):
        old_model = self.ui.listFeedList.model()
        model = FeedListModel(data=content, controller=self)
        self.ui.listFeedList.setModel(model)
        del old_model
    
    def activate_entry(self, index):
        """
        Action when an entry is selected
        """
        item = index.model().listdata[index.row()]
        self.get_selected(item)
        if hasattr(item, 'label'):
            self.set_current_category(item)
        else:
            self.ui_controller.display_feed(item)
        
    def set_current_category(self, category=None):
        """
        Set the new current category and update the feed list
        """
        if category is None and self.current_category is None:
            return
        if category is not None and self.current_category is not None \
        and category.id == self.current_category.id:
            self.current_category = None
        else:
            self.current_category = category
        if self.settings['feeds']['default'] == 'labels':
            self.update_feed_list()

    def verify_current_category(self):
        if not self.current_category:
            return
        if self.current_category.id != 'specials' \
        and self.current_category.id not in [c.id for c in self.gread.get_categories(self.show_updated)]:
            self.current_category = None

    def toggle_show_updated(self, checked):
        """
        Action when the "show updated" button is checked or unchecked
        """
        self.ui.menuBar.setDisabled(True)
        self.show_updated = checked
        self.verify_current_category()
        self.update_feed_list()
        self.ui.menuBar.setDisabled(False)
        
    def get_selected(self, item=None):
        if item is None:
            try:
                index = self.ui.listFeedList.selectedIndexes()[0]
            except:
                pass
            else:
                item = index.model().listdata[index.row()]

        if item is not None:
            if hasattr(item, 'label'):
                self.selected_category = item
                self.selected_feed = None
            else:
                self.selected_category = self.current_category
                self.selected_feed = item

    def trigger_sync(self, *args, **kwargs):
        """
        Action when the "sync" button is triggered
        """
        self.start_loading()
        self.get_selected()
        self.ui.menuBar.setDisabled(True)

        operation = Operation(
            action  = (self.gread.sync, {}), 
            name    = 'Sync feed list', 
            signal_done  = ('sync_done', []), 
            signal_error = ('sync_error', []),
            max_same = 1, 
            max_nb_tries = 5, 
        )
        operation.manage(self.operation_manager)

            
    def sync_done(self, sync_ok):
        """
        Actions when sync is done
        """
        if sync_ok:
            self.update_title()
            self.verify_current_category()
            self.update_feed_list()
            self.action_show_all.setDisabled(False)
            self.action_show_updated.setDisabled(False)
        self.ui.menuBar.setDisabled(False)
        self.stop_loading()
            
    def settings_updated(self):
        super(FeedListController, self).settings_updated()
        self.action_sync.setDisabled(not self.gread.auth_settings_ready())
        if self.gread.auth_settings_ready():
            self.update_feed_list()

    def show(self, app_just_launched=False):
        super(FeedListController, self).show(app_just_launched)
        if app_just_launched:
            if self.settings['google']['verified']:
                self.trigger_sync()
            else:
                self.trigger_settings()

    def get_title(self):
        return "%s (%d)" % (QApplication.applicationName(), self.gread.total_unread)

    def update_category(self, category):
        try:
            index = self.ui.listFeedList.model().index_of(category)
            self.ui.listFeedList.update(index)
        except:
            pass
        try:
            self.update_feed(category.category_feed, update_categories=False)
        except:
            pass

    def update_feed(self, feed, update_categories=True):
        try:
            index = self.ui.listFeedList.model().index_of(feed)
            # TODO: missing a way to insert row, don't know how to add data with insertRows
            # see https://svn.enthought.com/svn/enthought/TraitsBackendQt/trunk/enthought/traits/ui/qt4/list_str_model.py
#            if not feed.unread and self.show_updated:
#                self.ui.listFeedList.removeRow(index.row())
#            else:
            self.ui.listFeedList.update(index)
        except:
            pass
        for category in feed.getCategories():
            self.update_category(category)
        self.update_title()


class ItemListController(WindowController):
    def __init__(self, ui_controller):
        super(ItemListController, self).__init__(ui_controller, Ui_winItemList, ui_controller.feedlist_controller.win)

        self.current_feed = None
        self.selected_item = None

        self.show_updated_default = True
        self.show_mode_save       = True
        self.settings_updated()

        # menu bar

        # menu boutons : group for show all/updated
        self.group_show = QActionGroup(self.win)
        self.action_show_all = QAction("Show all", self.group_show)
        self.action_show_all.setCheckable(True)
        self.action_show_all.setDisabled(True)
        self.action_show_updated = QAction("Show updated", self.group_show)
        self.action_show_updated.setCheckable(True)
        self.action_show_updated.setDisabled(True)
        if self.show_updated_default:
            self.action_show_updated.setChecked(True)
        else:
            self.action_show_all.setChecked(True)
        self.ui.menuBar.addActions(self.group_show.actions())
        self.action_show_updated.toggled.connect(self.toggle_show_updated)
        
        # other menu boutons
        self.action_refresh = QAction("Refresh", self.win)
        self.action_refresh.setObjectName('actionRefresh')
        self.ui.menuBar.addAction(self.action_refresh)
        self.action_refresh.triggered.connect(self.trigger_refresh)

        self.action_fetch_more = QAction("Fetch more", self.win)
        self.action_fetch_more.setObjectName('actionFetchMore')
        self.ui.menuBar.addAction(self.action_fetch_more)
        self.action_fetch_more.triggered.connect(self.trigger_fetch_more)

        self.action_unsubscribe = QAction("Unsubscribe", self.win)
        self.action_unsubscribe.setObjectName('actionUnsubscribe')
        self.ui.menuBar.addAction(self.action_unsubscribe)
        self.action_unsubscribe.triggered.connect(self.trigger_unsubscribe)

        self.action_mark_all_read = QAction("Mark all as read", self.win)
        self.action_mark_all_read.setObjectName('actionMarkAllRead')
        self.ui.menuBar.addAction(self.action_mark_all_read)
        self.action_mark_all_read.triggered.connect(self.trigger_mark_all_read)

        self.ui.menuBar.setDisabled(True)

        # item list
        ilm = ItemListModel(data=[], controller=self)
        ild = ItemListDelegate(self.win)
        self.ui.listItemList.setModel(ilm)
        self.ui.listItemList.setItemDelegate(ild)
        self.ui.listItemList.activated.connect(self.activate_item)

        # operation signals
        QObject.connect(self.operation_manager, SIGNAL("get_feed_content_done"), self.feed_content_retrieved, Qt.QueuedConnection)
        QObject.connect(self.operation_manager, SIGNAL("get_feed_content_error"), self.feed_content_retrieved, Qt.QueuedConnection)
        QObject.connect(self.operation_manager, SIGNAL("get_more_feed_content_done"), self.feed_content_retrieved, Qt.QueuedConnection)
        QObject.connect(self.operation_manager, SIGNAL("get_more_feed_content_error"), self.feed_content_retrieved, Qt.QueuedConnection)

    def show_updated_only(self):
        return getattr(self.current_feed, 'show_updated', self.show_updated_default)

    def toggle_show_updated(self, checked):
        """
        Action when the "show updated" button is checked or unchecked
        """
        self.current_feed.show_updated = checked
        self.update_item_list()
        
    def get_selected(self, item=None):
        if item is None:
            try:
                index = self.ui.listItemList.selectedIndexes()[0]
            except:
                pass
            else:
                item = index.model().listdata[index.row()]
        if item is not None:
            self.selected_item = item
        
    def set_selected(self, item=None):
        if item is None:
            item = self.selected_item
        else:
            self.selected_item = item
        if item:
            index = self.ui.listItemList.model().index_of(item)
            if index:
                self.ui.listItemList.setCurrentIndex(index)
        
    def trigger_refresh(self):
        self.get_selected()
        self.update_item_list()
        
    def set_current_feed(self, feed):
        self.current_feed = feed
        self.action_mark_all_read.setDisabled(feed.unread == 0)
        self.update_title()
        self.update_item_list()
        return True
        
    def get_title(self):
        title = ""
        if self.current_feed:
            if self.current_feed.unread:
                title = "%s (%d)" % (self.current_feed.title, self.current_feed.unread)
            else:
                title = self.current_feed.title
        return title
        
    def update_item_list(self):
        """
        Empty and then refill the items' feed with current options
        """
        self.start_loading()
        self.update_listview(content=[])
        self.ui.menuBar.setDisabled(True)
        self.current_feed.clearItems()

        operation = Operation(
            action  = (self.gread.get_feed_content, {'feed': self.current_feed, 'updated_only': self.show_updated_only(),}), 
            name    = 'Get content for %s' % (self.current_feed.id, ), 
            signal_done  = ('get_feed_content_done',   [self.current_feed.id]), 
            signal_error = ('get_feed_content_error', [self.current_feed.id]),
        )
        operation.manage(self.operation_manager)
            
    def trigger_fetch_more(self):
        
        self.start_loading()
        self.get_selected()
        self.ui.menuBar.setDisabled(True)

        operation = Operation(
            action  = (self.gread.get_more_feed_content, {'feed': self.current_feed, 'updated_only': self.show_updated_only(),}), 
            name    = 'Get more content for %s' % (self.current_feed.id, ), 
            signal_done  = ('get_more_feed_content_done',   [self.current_feed.id]), 
            signal_error = ('get_more_feed_content_error', [self.current_feed.id]),
            max_same = 1, 
        )
        operation.manage(self.operation_manager)
        
    def feed_content_retrieved(self, feed_id):
        if feed_id != self.current_feed.id:
            return
        if not self.current_feed.lastLoadOk:
            self.ui_controller.display_message("Feed content could not be retrieved", level="critical")
        else:
            self.update_listview(content=self.current_feed.getItems())

        self.action_show_all.setDisabled(False)
        self.action_show_updated.setDisabled(False)
        self.ui.menuBar.setDisabled(False)

        if self.show_updated_only():
            self.action_show_updated.setChecked(True)
        else:
            self.action_show_all.setChecked(True)
            
        self.action_fetch_more.setDisabled(self.current_feed.continuation is None)

        self.stop_loading()

        # restore selection
        self.set_selected()

    def update_listview(self, content=[]):
        old_model = self.ui.listItemList.model()
        model = ItemListModel(data=content, controller=self)
        self.ui.listItemList.setModel(model)
        del old_model
        
    def activate_item(self, index):
        item = index.model().listdata[index.row()]
        self.get_selected(item)
        self.ui_controller.display_item(item)
        
    def activate_next_item(self):
        item = self.ui.listItemList.model().get_next(self.selected_item)
        if item:
            self.set_selected(item)
            self.ui_controller.display_item(item)
        else:
            self.ui_controller.display_message("No more message, please fetch more !")

    def activate_previous_item(self):
        item = self.ui.listItemList.model().get_previous(self.selected_item)
        if item:
            self.set_selected(item)
            self.ui_controller.display_item(item)
        else:
            self.ui_controller.display_message("No more message, you're at the top of the list")
        
    def settings_updated(self):
        super(ItemListController, self).settings_updated()
        self.show_updated_default = str(self.gread.settings['items']['show_mode']).find('updated') != -1
        self.show_mode_save       = str(self.gread.settings['items']['show_mode']).find('nosave') == -1

    def update_item(self, item):
        try:
            index = self.ui.listItemList.model().index_of(item)
            # TODO: missing a way to insert row, don't know how to add data with insertRows
            # see https://svn.enthought.com/svn/enthought/TraitsBackendQt/trunk/enthought/traits/ui/qt4/list_str_model.py
            #if item.isRead() and self.show_updated_only():
            #    self.ui.listItemList.model().removeRow(index.row())
            #else:
            self.ui.listItemList.update(index)
        except:
            raise
            pass
        self.update_title()

    def trigger_mark_all_read(self):
        # done in item methods but called asynchronously so we didi it now for refreshing the ui
        self.current_feed.unread = 0
        for item in self.current_feed.getItems():
            item.read = True
        for category in self.current_feed.getCategories():
            category.countUnread()
            try:
                category.category_feed.countUnread()
            except:
                pass
        # refreshing the ui
        self.ui_controller.feed_read(self.current_feed)
        # create the operation for marking as read asynchronously
        operation = Operation(
            action  = (self.gread.feed_mark_read, {'feed': self.current_feed}), 
            name    = "Mark feed %s as read" % self.current_feed.id, 
            signal_done  = ('feed_mark_read_done',   [self.current_feed.id]), 
            signal_error = ('feed_mark_read_error', [self.current_feed.id]),
        )
        operation.manage(self.operation_manager)
        
    def update_all_items(self):
        self.action_mark_all_read.setDisabled(True)
        for item in self.current_feed.getItems():
            self.update_item(item)
            
    def trigger_unsubscribe(self):
        self.ui_controller.display_message('Not yet implemented, sorry...')

class ItemViewEventFilter(QObject):
    def __init__(self, parent=None):
        QObject.__init__(self, parent)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            key = event.key()
            if key == Qt.Key_F7:
                self.emit(SIGNAL("zoom"), True)
                return True
            elif key == Qt.Key_F8:
                self.emit(SIGNAL("zoom"), False)
                return True
            elif key in (Qt.Key_J, Qt.Key_N):
                self.emit(SIGNAL("next"))
                return True
            elif key in (Qt.Key_K, Qt.Key_P):
                self.emit(SIGNAL("previous"))
                return True
        return QObject.eventFilter(self, obj, event)

class ItemViewController(WindowController):
    def __init__(self, ui_controller):
        super(ItemViewController, self).__init__(ui_controller, Ui_winItemView, ui_controller.itemlist_controller.win)
        
        # web view
        if MAEMO5_PRESENT:
            self.suppressor = QWebViewSelectionSuppressor(self.ui.webView)
            self.suppressor.enable()
            scroller = self.ui.webView.property("kineticScroller").toPyObject()
            if scroller:
                scroller.setEnabled(True)
            if MAEMO5_ZOOMKEYS:
                try:
                    grab_zoom_keys(self.win.winId(), True)
                except Exception, e:
                    pass
        self.ui.webView.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        self.ui.webView.page().linkClicked.connect(self.link_clicked)
        self.ui.webView.loadFinished.connect(self.trigger_web_view_loaded)
        
        # events
        self.eventFilter = ItemViewEventFilter(self.win)
        self.win.installEventFilter(self.eventFilter)
        QObject.connect(self.eventFilter, SIGNAL("zoom"), self.zoom)
        QObject.connect(self.eventFilter, SIGNAL("next"), self.show_next)
        QObject.connect(self.eventFilter, SIGNAL("previous"), self.show_previous)
        
        # menu bar : starred
        self.action_starred = QAction("Starred", self.win)
        self.action_starred.setObjectName('actionStarred')
        self.ui.menuBar.addAction(self.action_starred)
        self.action_starred.setCheckable(True)
        self.action_starred.triggered.connect(self.trigger_starred)
        # menu bar : shared
        self.action_shared = QAction("Shared", self.win)
        self.action_shared.setObjectName('actionShared')
        self.ui.menuBar.addAction(self.action_shared)
        self.action_shared.setCheckable(True)
        self.action_shared.triggered.connect(self.trigger_shared)
        # menu bar : mark read/unread
        self.action_mark_read = QAction("Mark read", self.win)
        self.action_mark_read.setObjectName('actionMarkRead')
        self.ui.menuBar.addAction(self.action_mark_read)
        self.action_mark_read.setCheckable(True)
        self.action_mark_read.triggered.connect(self.trigger_mark_read)
        # menu bar : see original
        self.action_see_original_browser = QAction("See original in Browser", self.win)
        self.action_see_original_browser.setObjectName('actionSeeOriginalBrowser')
        self.ui.menuBar.addAction(self.action_see_original_browser)
        self.action_see_original_browser.triggered.connect(self.trigger_see_original_browser)
        self.action_see_original_gread = QAction("See original in GRead", self.win)
        self.action_see_original_gread.setObjectName('actionSeeOriginalGRead')
        self.ui.menuBar.addAction(self.action_see_original_gread)
        self.action_see_original_gread.triggered.connect(self.trigger_see_original_gread)
        # menu bar : return to item
        self.action_return_to_item = QAction("Return to entry", self.win)
        self.action_return_to_item.setObjectName('actionReturnToItem')
        self.ui.menuBar.addAction(self.action_return_to_item)
        self.action_return_to_item.triggered.connect(self.trigger_return_to_item)

        self.current_item = None

    def set_current_item(self, item):
        self.start_loading()

        self.current_item = item
        self.update_title()
        if not item.isRead():
            self.trigger_mark_read(True)

        # menus
        self.action_mark_read.setChecked(item.isRead())
        self.action_mark_read.setDisabled(not item.canUnread)
        self.action_shared.setChecked(item.isShared())
        self.action_starred.setChecked(item.isStarred())
            
        self.action_see_original_gread.setDisabled(item.url is None)
        self.action_see_original_gread.setVisible(True)
        self.action_see_original_browser.setDisabled(item.url is None)
        self.action_see_original_browser.setVisible(True)
        self.action_return_to_item.setDisabled(True)
        self.action_return_to_item.setVisible(False)
            
        # display content
        if MAEMO5_PRESENT:
            self.ui_controller.display_message(item.title)
        self.ui.webView.setHtml(item.content)
        return True

    def trigger_mark_read(self, checked):
        if checked != self.current_item.isRead():
            # done in item methods but called asynchronously so we didi it now for refreshing the ui
            self.current_item.parent.markItemRead(self.current_item, checked)
            self.current_item.read = checked
            for category in self.current_item.parent.getCategories():
                try:
                    category.category_feed.countUnread()
                except:
                    pass
            # refreshing the ui
            self.ui_controller.item_read(self.current_item, checked)
            # create the operation for marking as read asynchronously
            action = self.gread.item_mark_read
            action_str = 'read'
            if not checked:
                action = self.gread.item_mark_unread
                action_str = 'unread'
            operation = Operation(
                action  = (action, {'item': self.current_item}), 
                name    = 'Mark item %s as %s' % (self.current_item.id, action_str), 
                signal_done  = ('item_mark_read_done',   [self.current_item.id]), 
                signal_error = ('item_mark_read_error', [self.current_item.id]),
            )
            operation.manage(self.operation_manager)

    def trigger_shared(self, checked):
        if checked != self.current_item.isShared():
            self.ui_controller.item_shared(self.current_item, checked)
            action = self.gread.item_share
            action_str = 'shared'
            if not checked:
                action = self.gread.item_unshare
                action_str = 'unshared'
            operation = Operation(
                action  = (action, {'item': self.current_item}), 
                name    = 'Mark item %s as %s' % (self.current_item.id, action_str), 
                signal_done  = ('item_shared_done',   [self.current_item.id]), 
                signal_error = ('item_shared_error', [self.current_item.id]),
            )
            operation.manage(self.operation_manager)

    def trigger_starred(self, checked):
        if checked != self.current_item.isStarred():
            self.ui_controller.item_starred(self.current_item, checked)
            action = self.gread.item_star
            action_str = 'starred'
            if not checked:
                action = self.gread.item_unstar
                action_str = 'unstarred'
            operation = Operation(
                action  = (action, {'item': self.current_item}), 
                name    = 'Mark item %s as %s' % (self.current_item.id, action_str), 
                signal_done  = ('item_starred_done',   [self.current_item.id]), 
                signal_error = ('item_starred_error', [self.current_item.id]),
            )
            operation.manage(self.operation_manager)
        
    def trigger_see_original_gread(self):
        self.open_url(QUrl(self.current_item.url), force_in_gread=True, zoom_gread=1.0)

    def trigger_see_original_browser(self):
        self.open_url(QUrl(self.current_item.url))
            
    def trigger_return_to_item(self):
        self.action_see_original_gread.setDisabled(False)
        self.action_see_original_gread.setVisible(True)
        self.action_return_to_item.setDisabled(True)
        self.action_return_to_item.setVisible(False)
        self.ui.webView.setHtml(self.current_item.content)

    def open_url(self, url, force_in_gread=False, zoom_gread=None):
        if force_in_gread or not QDesktopServices.openUrl(url):
            self.ui.webView.setHtml("")
            self.start_loading()
            self.action_see_original_gread.setDisabled(True)
            self.action_see_original_gread.setVisible(False)
            self.action_return_to_item.setDisabled(False)
            self.action_return_to_item.setVisible(True)
            if zoom_gread is not None:
                self.ui.webView.setZoomFactor(zoom_gread)
            self.ui.webView.load(url)
            return False
        return True
        
    def link_clicked(self, url):
        self.open_url(url)
                        
    def get_title(self):
        title = ""
        if self.current_item:
            title = self.current_item.title
        return title

    def zoom(self, zoom_in=True):
        factor = 1.1
        if not zoom_in:
            factor = 1/1.1
        self.ui.webView.setZoomFactor(self.ui.webView.zoomFactor()*factor)
        
    def trigger_web_view_loaded(self, ok):
        self.stop_loading()
        
    def show_next(self):
        item = self.ui_controller.display_next_item()
        
    def show_previous(self):
        item = self.ui_controller.display_previous_item()
            
class UiController(object):
    def __init__(self, gread):
        """
        Constructor
        """
        self.gread = gread
        self.settings = gread.settings
        self.operation_manager = gread.operation_manager
        
        self.portrait_mode = False
        self.set_portrait_mode()

        if MAEMO5_PRESENT:
            self.title_timer = QTimer()
            QObject.connect(self.title_timer, SIGNAL("timeout()"), self.timeout_title_timer)

        self.controllers = []
        self.feedlist_controller = FeedListController(self)
        self.itemlist_controller = ItemListController(self)
        self.itemview_controller = ItemViewController(self)
        self.current = self.feedlist_controller
        
        QObject.connect(self.operation_manager, SIGNAL("operation_added"), self.update_titles, Qt.QueuedConnection)
        QObject.connect(self.operation_manager, SIGNAL("operation_stop_running"), self.update_titles, Qt.QueuedConnection)
        QApplication.desktop().resized.connect(self.trigger_desktop_resized)
        

    def set_portrait_mode(self):
        if MAEMO5_PRESENT and self.gread.settings['other']['auto_rotation']:
            geo = QApplication.desktop().screenGeometry()
            self.portrait_mode = geo.height() > geo.width()
            return self.portrait_mode
        return False

    def trigger_desktop_resized(self):
        if self.current and MAEMO5_PRESENT and self.gread.settings['other']['auto_rotation']:
            self.set_portrait_mode()
            try:
                self.current.update_title()
            except:
                pass
        
    def add_controller(self, controller):
        self.controllers.append(controller)
        
    def show(self, app_just_launched=False):
        self.current.show(app_just_launched)
        
    def get_title_operations_part(self):
        nb = self.operation_manager.get_nb_operations()
        if nb:
            if MAEMO5_PRESENT:
                return "%d" % nb
            else:
                return "%d operations" % nb
        else:
            return ""
            
    def update_titles(self):
        for controller in self.controllers:
            controller.update_title()
            
    def timeout_title_timer(self):
        self.current.update_display_title()

    def hide_children(self, controller):
        for child in self.controllers:
            if child.win.parent() == controller.win and child.win.isVisible():
                self.hide_children(child)
                child.win.hide()

    def set_current(self, controller):
        if controller != self.current:
            old_current = self.current
            self.current = controller
            self.hide_children(self.current)
            self.current.show()
        
    def switch_win(self, name):
        if name == 'feedlist':
            controller = self.feedlist_controller
        elif name == 'itemlist':
            controller = self.itemlist_controller
        elif name == 'itemview':
            controller = self.itemview_controller
        else:
            return
        self.set_current(controller)
        
    def display_message(self, message, level="information"):
        """
        Display a message for a level ([information|warning|critical]), and handle the
        Maemo5 special case
        """
        if MAEMO5_PRESENT:
            QMaemo5InformationBox.information(self.current.win, '<p>%s</p>' % message, QMaemo5InformationBox.DefaultTimeout)
        else:
            box = QMessageBox(self.current.win)
            box.setText(message)
            box.setWindowTitle(QApplication.applicationName())
            if level == "critical":
                box.setIcon(QMessageBox.Critical)
            elif level == "warning":
                box.setIcon(QMessageBox.Warning)
            else:
                box.setIcon(QMessageBox.Information)
            box.exec_()
            
    def settings_updated(self):
        if not self.settings['other']['auto_rotation']:
            self.portrait_mode = False
        for controller in self.controllers:
            controller.settings_updated()
        
    def display_feed(self, feed):
        self.switch_win('itemlist')
        if not self.itemlist_controller.set_current_feed(feed):
            self.switch_win('feedlist', hide_current=True)
        
    def show_settings(self):
        self.feedlist_controller.trigger_settings()
        
    def start_loading(self):
        self.current.start_loading()
            
    def stop_loading(self):
        self.current.stop_loading()
            
    def sync_done(self, sync_ok):
        self.feedlist_controller.sync_done(sync_ok)
            
    def display_item(self, item):
        self.switch_win('itemview')
        if not self.itemview_controller.set_current_item(item):
            self.switch_win('itemlist', hide_current=True)
            
    def display_next_item(self):
        self.itemlist_controller.activate_next_item()
            
    def display_previous_item(self):
        self.itemlist_controller.activate_previous_item()

    def item_read(self, item, is_read):
        self.gread.count_unread()
        if self.itemlist_controller.current_feed == item.parent:
            self.itemlist_controller.update_item(item)
            self.feedlist_controller.update_feed(item.parent)
        
    def item_starred(self, item, is_starred):
        if self.itemlist_controller.current_feed == item.parent:
            self.itemlist_controller.update_item(item)
        
    def item_shared(self, item, is_shared):
        if self.itemlist_controller.current_feed == item.parent:
            self.itemlist_controller.update_item(item)

    def feed_read(self, feed):
        self.gread.count_unread()
        if self.itemlist_controller.current_feed == feed:
            self.itemlist_controller.update_all_items()
            self.feedlist_controller.update_feed(feed)
