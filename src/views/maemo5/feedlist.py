# -*- coding: utf-8 -*-

"""
Feed list view
"""
from PyQt4.QtGui import *
from PyQt4.QtCore import *
    
import time
    
from views.maemo5.ui.Ui_feedlist import Ui_winFeedList
from views.maemo5 import MAEMO5_PRESENT, ListModel, View

from engine import settings
from engine.models import *

class FeedListDelegate(QStyledItemDelegate):
    
    def sizeHint(self, option, index):
        size = super(FeedListDelegate, self).sizeHint(option, index)
        if MAEMO5_PRESENT:
            if size.height() != 70:
                size.setHeight(70)
            return size
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
        Paint the list item with the default options, then add the unread counter
        """
        painter.save()

        try:
            # item to work with
            is_category = False            
            model = index.model()
            item = model.listdata[index.row()]

            text_style_option = QStyleOptionViewItemV4(option)
            text_font = text_style_option.font
            if isinstance(item, Feed):
                # it's a feed
                text = item.title
                # add a blank to the left to mimic a treeview
                text_style_option.rect.adjust(15, 0, 0, 0)
                if item.__class__ != Feed:
                    text_font.setStyle(QFont.StyleItalic)
                if item.unread and not model.view.unread_only:
                    text_font.setWeight(QFont.Bold)
            else:
                # it's a category
                is_category = True
                text = item.title
                if item.unread and not model.view.unread_only:
                    text_font.setWeight(QFont.Bold)
                if isinstance(item, SpecialCategory):
                    text_font.setStyle(QFont.StyleItalic)

            # draw background and borders
            self.parent().style().drawControl(QStyle.CE_ItemViewItem, text_style_option, painter)

            # prepare the text_rect. Will be reduced for displaying unread count
            text_rect  = text_style_option.rect

            # display unread count
            if item.unread:
                if is_category:
                    str_unread = "%d/%d" % (item.unread, item.count_feeds(unread_only=True))
                else:
                    str_unread = "%d" % item.unread
                palette = text_style_option.palette
                unread_rect = painter.boundingRect(option.rect, Qt.AlignRight | Qt.AlignVCenter, str_unread)
                unread_rect.adjust(-8, -3, -2, +3)
                painter.setBrush(QBrush(palette.color(palette.Highlight)))
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
            text_rect.adjust(8, 4, 0, -4)
            painter.drawText(QRectF(text_rect), text, text_option)
            
            # draw a bar for unread category/feeds
            if item.unread:# and not model.view.unread_only:
                bar_option = QStyleOptionViewItemV4(option)
                if is_category:
                    bar_option.rect.setLeft(1)
                else:
                    bar_option.rect.setLeft(16)
                bar_option.rect.setWidth(1)
                bar_option.rect.adjust(0, 1, 0, -1)
                painter.setPen(palette.color(palette.Highlight))
                painter.setBrush(QBrush(palette.color(palette.Highlight)))
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

class FeedListView(View):
    def __init__(self, controller):
        super(FeedListView, self).__init__(controller, Ui_winFeedList)
        
        self.current_category = None
        self.unread_only     = settings.get('feeds', 'unread_only')

        self.selected_category = None
        self.selected_feed     = None

        # menu bar

        self.add_orientation_menu()
        
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
        self.action_show_unread_only.toggled.connect(self.toggle_unread_only)
        
        # feed list
        flm = FeedListModel(data=[], view=self)
        fld = FeedListDelegate(self.win)
        self.ui.listFeedList.setModel(flm)
        self.ui.listFeedList.setItemDelegate(fld)
        self.ui.listFeedList.activated.connect(self.activate_entry)
        
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

    
    def activate_entry(self, index):
        """
        Action when an entry is selected
        """
        item = index.model().listdata[index.row()]
        self.get_selected(item)
        if isinstance(item, Category):
            self.set_current_category(item)
        else:
            self.controller.display_feed(item)
        
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

    def toggle_unread_only(self, checked):
        """
        Action when the "show unread" button is checked or unchecked
        """
        self.get_selected()
        self.unread_only = checked
        self.verify_current_category()
        self.update_feed_list()

    def get_selected(self, item=None):
        """
        Save the current selected item for select it back when the list will
        be refreshed
        """
        if item is None:
            try:
                index = self.ui.listFeedList.selectedIndexes()[0]
            except:
                pass
            else:
                item = index.model().listdata[index.row()]

        if item is not None:
            if isinstance(item, Category):
                self.selected_category = item
                self.selected_feed = None
            else:
                self.selected_category = self.current_category
                self.selected_feed = item

    def trigger_sync(self, *args, **kwargs):
        """
        Action when the "sync" button is triggered
        """
        self.feeds_fetching_started()        
        self.controller.account.fetch_feeds(fetch_unread_content=True)
        
    def feeds_fetching_started(self):
        """
        Actions when feed's fetching starts
        """
        self.start_loading()
        self.update_title()
        self.action_settings.setDisabled(True)
        self.action_sync.setDisabled(True)
            
    def feeds_fetched(self):
        """
        Actions when feeds are just fetched
        """
        self.update_title()
        self.verify_current_category()
        self.get_selected()
        self.update_feed_list()
        self.action_show_all.setDisabled(False)
        self.action_show_unread_only.setDisabled(False)
        self.action_settings.setDisabled(False)
        self.action_sync.setDisabled(False)
        self.stop_loading()
            
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
        for category in feed.categories:
            self.update_category(category)

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
