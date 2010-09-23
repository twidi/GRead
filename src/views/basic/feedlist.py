# -*- coding: utf-8 -*-

"""
Feed list view
"""
from PyQt4.QtGui import *
from PyQt4.QtCore import *
    
import time
    
from ui.Ui_feedlist import Ui_winFeedList
from . import ListModel, View, ViewEventFilter, base_view_class, base_eventfilter_class

from engine import settings
from engine.models import *

class FeedListDelegate(QStyledItemDelegate):
    
    def sizeHint(self, option, index):
        size = super(FeedListDelegate, self).sizeHint(option, index)
        try:
            metrics = QFontMetrics(option.font)
            min_height = metrics.height() +10
            if size.height() < min_height:
                size.setHeight(min_height)
        except:
            pass
        return size
        

    def paint(self, painter, option, index):
        """
        Paint the list entry with the default options, then add the unread counter
        """
        painter.save()
        
        try:
            # entry to work with
            is_category = False            
            model = index.model()
            entry = model.listdata[index.row()]

            text_style_option = QStyleOptionViewItemV4(option)
            palette = text_style_option.palette
            text_font = text_style_option.font
            if isinstance(entry, Feed):
                # it's a feed
                text = entry.title
                # add a blank to the left to mimic a treeview
                text_style_option.rect.adjust(15, 0, 0, 0)
                if entry.__class__ != Feed:
                    text_font.setStyle(QFont.StyleItalic)
                if entry.unread and not model.view.unread_only:
                    text_font.setWeight(QFont.Bold)
            else:
                # it's a category
                is_category = True
                text = entry.title
                if entry.unread and not model.view.unread_only:
                    text_font.setWeight(QFont.Bold)
                if isinstance(entry, SpecialCategory):
                    text_font.setStyle(QFont.StyleItalic)

            # draw background and borders
            self.parent().style().drawControl(QStyle.CE_ItemViewItem, text_style_option, painter)

            # prepare the text_rect. Will be reduced for displaying unread count
            text_rect  = text_style_option.rect

            # display unread count
            if entry.unread:
                if is_category:
                    if isinstance(entry, SpecialCategory):
                        count = sum([1 for special_type in settings.special_feeds\
                            if settings.get('feeds', 'show_%s' % special_type) and entry.special_feeds[special_type].unread])
                    else:
                        count = entry.count_feeds(unread_only=True)
                    str_unread = "%d/%d" % (entry.unread, count)
                else:
                    str_unread = "%d" % entry.unread
                unread_rect = painter.boundingRect(option.rect, Qt.AlignRight | Qt.AlignVCenter, str_unread)
                unread_rect.adjust(-8, -3, -2, +3)
                painter.setBrush(palette.highlight())
                painter.setPen(palette.color(palette.Highlight))
                painter.setRenderHint(QPainter.Antialiasing);
                painter.drawRoundedRect(unread_rect, 4, 4);
                painter.setPen(palette.color(palette.HighlightedText))
                painter.drawText(unread_rect, Qt.AlignCenter | Qt.AlignVCenter, str_unread)
                text_rect.adjust(0, 0, -(unread_rect.width()+4), 0)

            # display category/feed title
            painter.restore()
            painter.save()
            text_option = QTextOption(Qt.AlignLeft | Qt.AlignVCenter)
            text_option.setWrapMode(QTextOption.WordWrap)
            painter.setFont(text_font)
            if option.state & QStyle.State_Selected:
                painter.setPen(palette.color(palette.HighlightedText))
            text_rect.adjust(8, 4, 0, -4)
            painter.drawText(QRectF(text_rect), text, text_option)
            
            # draw a bar for unread category/feeds
            if entry.unread:# and not model.view.unread_only:
                bar_option = QStyleOptionViewItemV4(option)
                if is_category:
                    bar_option.rect.setLeft(1)
                else:
                    bar_option.rect.setLeft(16)
                bar_option.rect.setWidth(1)
                bar_option.rect.adjust(0, 1, 0, -1)
                painter.setPen(palette.color(palette.Highlight))
                painter.setBrush(palette.highlight())
                painter.setRenderHint(QPainter.Antialiasing);
                painter.drawRoundedRect(bar_option.rect, 4, 4);

        finally:
            painter.restore()

class FeedListModel(ListModel):        
    def data(self, index, role):
        if index.isValid() and role == Qt.DisplayRole:
            return QVariant(self.listdata[index.row()].title)
        else:
            return QVariant()

class FeedListEventFilter(base_eventfilter_class):
    def eventFilter(self, obj, event):
        if super(FeedListEventFilter, self).eventFilter(obj, event):
            return True
        if event.type() == QEvent.KeyPress:
            key = event.key()
            if key == Qt.Key_S and self.isShift(event):
                self.emit(SIGNAL("trigger_sync"), True)
                return True
            elif key == Qt.Key_Backspace:
                self.emit(SIGNAL("trigger_back"), True)
                return True
            elif key == Qt.Key_O and not self.isShift(event):
                self.emit(SIGNAL("trigger_open"), True)
                return True
            elif key == Qt.Key_U:
                self.emit(SIGNAL("toggle_unread_only"))
                return True
            elif event.modifiers() & Qt.ShiftModifier and \
                (key == Qt.Key_A or key == Qt.Key_M):
                self.emit(SIGNAL("mark_selected_all_read"))
                return True
            elif key in (Qt.Key_J, Qt.Key_N):
                self.emit(SIGNAL("select_next"))
                return True
            elif key in (Qt.Key_K, Qt.Key_P):
                self.emit(SIGNAL("select_previous"))
                return True
        return QObject.eventFilter(self, obj, event)

class FeedListView(base_view_class):
    def __init__(self, controller):
        self.current_category = None
        self.unread_only     = settings.get('feeds', 'unread_only')

        self.selected_category = None
        self.selected_feed     = None
        
        self.sync_running = False

        super(FeedListView, self).__init__(controller, self.get_ui_class())
        
        # feed list
        flm = FeedListModel(data=[], view=self)
        fld = self.get_feedlist_delegate_class()(self.win)
        self.ui.listFeedList.setModel(flm)
        self.ui.listFeedList.setItemDelegate(fld)
        self.ui.listFeedList.activated.connect(self.activate_entry)

    def get_ui_class(self):
        return Ui_winFeedList
        
    def get_feedlist_delegate_class(self):
        return FeedListDelegate

    def init_menu(self):
        super(FeedListView, self).init_menu()
        
        # simple menu boutons
        self.action_settings = QAction("Settings", self.win)
        self.action_settings.setObjectName('actionSettings')
        self.action_sync = QAction("Synchronize all", self.win)
        self.action_sync.setDisabled(not settings.auth_ready())
        self.action_sync.setObjectName('actionSync')
        self.ui.menuBar.addAction(self.action_settings)
        self.ui.menuBar.addAction(self.action_sync)
        self.action_settings.triggered.connect(self.controller.trigger_settings)
        self.action_sync.triggered.connect(self.trigger_sync)

        # menu boutons : group for show all/unread
        self.group_show = QActionGroup(self.win)
        self.action_show_all = QAction("Show all", self.group_show)
        self.action_show_all.setCheckable(True)
        self.action_show_all.setDisabled(True)
        self.action_show_unread_only = QAction("Show unread", self.group_show)
        self.action_show_unread_only.setCheckable(True)
        self.action_show_unread_only.setDisabled(True)
        if settings.get('feeds', 'unread_only'):
            self.action_show_unread_only.setChecked(True)
        else:
            self.action_show_all.setChecked(True)
        self.ui.menuBar.addActions(self.group_show.actions())
        self.action_show_unread_only.toggled.connect(self.trigger_unread_only)
        
        # context menu
        self.make_context_menu(self.ui.listFeedList)
        
        self.action_mark_selected_as_read = QAction("Mark as read", self.win)
        self.action_mark_selected_as_read.triggered.connect(self.trigger_mark_selected_as_read)
        self.context_menu.addAction(self.action_mark_selected_as_read)

        self.context_menu.addSeparator()
        self.context_menu.addActions(self.group_show.actions())
        self.context_menu.addSeparator()
        self.context_menu.addAction(self.action_sync)
        self.context_menu.addAction(self.action_settings)
        
        self.manage_actions()

    def init_events(self):
        super(FeedListView, self).init_events()
        
        self.add_event_filter(self.ui.listFeedList, FeedListEventFilter)
        QObject.connect(self.event_filter, SIGNAL("trigger_sync"), self.trigger_sync)
        QObject.connect(self.event_filter, SIGNAL("trigger_back"), self.trigger_back)
        QObject.connect(self.event_filter, SIGNAL("trigger_open"), self.trigger_open)
        QObject.connect(self.event_filter, SIGNAL("toggle_unread_only"), self.toggle_unread_only)
        QObject.connect(self.event_filter, SIGNAL("mark_selected_all_read"), self.trigger_mark_selected_as_read)        
        QObject.connect(self.event_filter, SIGNAL("select_next"), self.select_next_entry)
        QObject.connect(self.event_filter, SIGNAL("select_previous"), self.select_previous_entry)
    
    def manage_actions(self):
        """
        Update the menus (main menu and context menu)
        """
        auth_ready = settings.auth_ready()
        self.action_sync.setDisabled(self.sync_running or not auth_ready)
        self.action_show_all.setDisabled(not auth_ready)
        self.action_show_unread_only.setDisabled(not auth_ready)
        self.action_show_unread_only.setChecked(self.unread_only)
        self.action_settings.setDisabled(self.sync_running or not auth_ready)          
        self.action_mark_selected_as_read.setDisabled(not self.can_mark_selected_as_read())
        
    def request_context_menu(self, pos):
        """
        Called when the user ask for the context menu to be displayed
        """
        super(FeedListView, self).request_context_menu(pos)
        self.get_selected()
        self.manage_actions()
        self.display_context_menu(pos)
        
    def update_feed_list(self):
        """
        Empty and then refill the feed list with current options
        """
        if not self.controller.account.is_authenticated:
            return
        self.update_listview(content=self.get_content(self.unread_only, self.current_category))
        self.set_selected()
        
    def set_selected(self):
        """
        Try to restore the selected category and feed in the list
        """
        if self.selected_category:
            category_index = self.ui.listFeedList.model().index_of(self.selected_category)
            if category_index:
                self.ui.listFeedList.setCurrentIndex(category_index)
                if self.selected_feed:
                    feed_index = self.ui.listFeedList.model().index_of(self.selected_feed, start=category_index.row()+1)
                    if feed_index:
                        self.ui.listFeedList.setCurrentIndex(feed_index)
                    else:
                        self.selected_feed = None
            else:
                self.selected_category = None

    def get_content(self, unread_only=False, current_category=None):
        """
        Compute the content to be displayed in the list.
        """
        result = []
        for category in self.controller.account.get_categories(unread_only=unread_only):
            result.append(category)
            if settings.get('feeds', 'default') == 'feeds' \
                or (current_category is not None and category == current_category):
                feed_unread_only = unread_only and not isinstance(category, SpecialCategory)
                feeds = category.get_feeds(unread_only=feed_unread_only)
                if category == self.controller.account.special_category:
                    s_feeds = [feed for feed in feeds if settings.get('feeds', 'show_%s' % feed.special_type)]
                    feeds = s_feeds
                for feed in feeds:
                    result.append(feed)
        return result

    def update_listview(self, content=[]):
        """
        Update the list widget
        """
        old_model = self.ui.listFeedList.model()
        model = FeedListModel(data=content, view=self)
        self.ui.listFeedList.setModel(model)
        del old_model

    def trigger_open(self):
        """
        Action when an "open" action is done on an entry
        """
        self.get_selected()
        if self.selected_feed:
            self.controller.display_feed(self.selected_feed)
        elif self.selected_category:
            self.set_current_category(self.selected_category)

    def activate_entry(self, index):
        """
        Action when an entry is selected
        """
        entry = index.model().listdata[index.row()]
        self.get_selected(entry)
        if isinstance(entry, Category):
            self.set_current_category(entry)
        else:
            self.controller.display_feed(entry)
        
    def set_current_category(self, category=None):
        """
        Set the new current category and update the feed list
        """
        if category is None and self.current_category is None:
            return
        if category is not None and self.current_category is not None \
            and category == self.current_category:
            # close the current category
            self.current_category = None
        else:
            self.current_category = category
        if settings.get('feeds', 'default') == 'labels':
            self.update_feed_list()

    def verify_current_category(self):
        """
        Verify if the current category must be kept, for instance, if it
        has no unread items and we display only unread ones, then it cannot be
        the current category
        """
        if not self.current_category:
            return
        if not isinstance(self.current_category, SpecialCategory) \
            and self.current_category not in self.controller.account.get_categories(unread_only=self.unread_only):
            self.current_category = None

    def trigger_unread_only(self, checked):
        """
        Action when the "show unread" button is checked or unchecked
        """
        if not settings.auth_ready():
            return
        if self.unread_only != checked:
            self.get_selected()
            self.unread_only = checked
            self.verify_current_category()
            self.update_feed_list()
        
    def toggle_unread_only(self):
        """
        Called when we want to toggle the display between all items or only 
        unread ones
        """
        self.action_show_unread_only.setChecked(not self.unread_only)

    def get_selected(self, entry=None):
        """
        Save the current selected entry for select it back when the list will
        be refreshed
        """
        if entry is None:
            try:
                index = self.ui.listFeedList.selectedIndexes()[0]
            except:
                pass
            else:
                entry = index.model().listdata[index.row()]

        if entry is not None:
            if isinstance(entry, Category):
                self.selected_category = entry
                self.selected_feed = None
            else:
                self.selected_category = self.current_category
                self.selected_feed = entry

    def trigger_back(self):
        """
        When "backspace" is clicked on a opened category, close it
        """
        self.get_selected()
        if self.selected_category:
            previous = self.ui.listFeedList.model().get_previous(self.selected_category)
            next     = self.ui.listFeedList.model().get_next(self.selected_category)
            if isinstance(next, Feed):
                self.set_current_category(self.selected_category)
                if not self.selected_category:
                    self.current_category  = previous
                    self.selected_category = previous
                    self.set_current_category(previous)
            

    def trigger_sync(self, *args, **kwargs):
        """
        Action when the "sync" button is triggered
        """
        if self.sync_running:
            return
        self.feeds_fetching_started()        
        self.controller.account.fetch_feeds(fetch_unread_content=True)
        
    def feeds_fetching_started(self):
        """
        Actions when feed's fetching starts
        """
        self.start_loading()
        self.sync_running = True
        self.manage_actions()
        self.update_title()
            
    def feeds_fetched(self):
        """
        Actions when feeds are just fetched
        """
        self.update_title()
        self.verify_current_category()
        self.get_selected()
        self.update_feed_list()
        self.sync_running = False
        self.manage_actions()
        self.stop_loading()
        if not self.selected_category:
            self.select_row(row=0)
                
    def select_row(self, row=None, entry=None):
        """
        Try to select an entry in the list, by a specific entry, or by a number
        """
        try:
            index = None
            model = self.ui.listFeedList.model()
            if entry:
                index = model.index_of(entry)
            if not index:
                if not row:
                    row = 0
                index = model.index(row)
            self.ui.listFeedList.setCurrentIndex(index)
        except:
            pass
            
    def settings_updated(self):
        """
        Called when settings are updated
        """
        super(FeedListView, self).settings_updated()
        self.unread_only = not not settings.get('feeds', 'unread_only')
        self.action_sync.setDisabled(not settings.auth_ready())
        if settings.auth_ready():
            self.update_feed_list()

    def show(self, app_just_launched=False):
        """
        Diplay the window and if the account is ok, launch a 
        sync, else display settings
        """
        super(FeedListView, self).show(app_just_launched)
        self.ui.listFeedList.setFocus(Qt.OtherFocusReason)
        if app_just_launched:
            if settings.get('google', 'verified'):
                self.trigger_sync()
            else:
                self.controller.trigger_settings()

    def get_title(self):
        """
        Get the title for this view : the app name and the total unread count
        """
        return "%s (%d)" % (QApplication.applicationName(), self.controller.account.unread)
        
    def feed_content_fetched(self, feed):
        """
        Called when a feed content was just fetched, to redraw the ui
        """
        self.update_feed(feed)
        if isinstance(feed, CategoryFeed):
            for other_feed in feed.categories[0].get_feeds(unread_only=self.unread_only):
                self.update_feed(other_feed)

    def update_category(self, category):
        """
        Called when a category is updated, to refresh it's entry in the list, 
        and it's category_feed if it has one
        """
        try:
            index = self.ui.listFeedList.model().index_of(category)
            self.ui.listFeedList.update(index)
        except:
            pass
        try:
            if category.category_feed:
                self.update_feed(category.category_feed, update_categories=False)
        except:
            pass
        self.update_title()

    def update_feed(self, feed, update_categories=True):
        """
        Called when a feed is updated, to refresh it's entry in the list, and all
        it's categories if wanted and if it has ones
        """
        try:
            index = self.ui.listFeedList.model().index_of(feed)
            # TODO: missing a way to insert row, don't know how to add data with insertRows
            # see https://svn.enthought.com/svn/enthought/TraitsBackendQt/trunk/enthought/traits/ui/qt4/list_str_model.py
#            if not feed.unread and self.unread_only:
#                self.ui.listFeedList.removeRow(index.row())
#            else:
            self.ui.listFeedList.update(index)
        except:
            pass
        if update_categories:
            for category in feed.categories:
                self.update_category(category)
        self.update_title()

    def item_read(self, item):
        """
        Called when an item was marked as read/unread
        """
        for feed in item.feeds:
            self.update_feed(feed)

    def item_shared(self, item):
        """
        Called when an item was shared/unshared
        """
        for feed in item.feeds:
            self.update_feed(feed)

    def item_starred(self, item):
        """
        Called when an item was starred/unstarred
        """
        for feed in item.feeds:
            self.update_feed(feed)

    def feed_read(self, feed):
        """
        Called when an feed was marked as read
        """
        self.update_feed(feed)
        
    def can_mark_selected_as_read(self):
        """
        Return True if the current category/feed can be marked as read
        """
        if self.selected_feed and self.selected_feed.unread:
            return True
        elif self.selected_category and self.selected_category.unread \
            and not isinstance(self.selected_category, (SpecialCategory, OrphanFeedsCategory)):
            return True
        return False
        
    def trigger_mark_selected_as_read(self):
        """
        Called when the selected category/feed must be marked as read
        """
        self.get_selected()
        if self.can_mark_selected_as_read():
            if self.selected_feed:
                self.selected_feed.mark_as_read()
                self.controller.feed_read(self.selected_feed)
            else:
                try:
                    self.selected_category.category_feed.mark_as_read()
                    self.controller.feed_read(self.selected_category.category_feed)
                except:
                    pass
            
    def select_next_entry(self):
        """
        Select the next entry in the list (but without activating it)
        Return True if the operation is successfull
        """
        self.get_selected()
        current = self.selected_feed
        if not current:
            current = self.selected_category
        entry = self.ui.listFeedList.model().get_next(current)
        if entry:
            if isinstance(entry, Category):
                self.selected_category = entry
                self.selected_feed     = None
            else:
                self.selected_feed = entry
            self.set_selected()
            current = self.selected_feed
            if not current:
                current = self.selected_category
            return not not current
        return False
            
    def select_previous_entry(self):
        """
        Select the previous entry in the list (but without activating it)
        Return True if the operation is successfull
        """
        self.get_selected()
        current = self.selected_feed
        if not current:
            current = self.selected_category
        entry = self.ui.listFeedList.model().get_previous(current)
        if entry:
            if isinstance(entry, Category):
                self.selected_category = entry
                self.selected_feed     = None
            else:
                self.selected_feed = entry
            self.set_selected()
            current = self.selected_feed
            if not current:
                current = self.selected_category
            return not not current
        return False
