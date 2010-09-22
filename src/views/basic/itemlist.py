# -*- coding: utf-8 -*-

"""
Item list view
"""
from PyQt4.QtGui import *
from PyQt4.QtCore import *
    
from ui.Ui_itemlist import Ui_winItemList
from . import ListModel, View, ViewEventFilter, base_view_class, base_eventfilter_class

from engine import settings
from engine.models import *

class ItemListDelegate(QStyledItemDelegate):
    
    def current_special_feed(self, view):
        if isinstance(view.current_feed, (SpecialFeed, CategoryFeed, )):
            return view.current_feed
        return None
    
    def sizeHint(self, option, index):
        size = super(ItemListDelegate, self).sizeHint(option, index)
        try:
            model = index.model()
            item = model.listdata[index.row()]
            metrics = QFontMetrics(option.font)
            min_height = metrics.height() + 8
            if self.current_special_feed(model.view):
                min_height = int(metrics.height() * 2.3) + 8
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

            # item to work with
            model = index.model()
            item = model.listdata[index.row()]
            special_feed = self.current_special_feed(model.view)

            # draw background and borders
            text_style_option = QStyleOptionViewItemV4(option)
            self.parent().style().drawControl(QStyle.CE_ItemViewItem, text_style_option, painter)

            # draw text
            text_font   =  text_style_option.font
            if item.unread:
                text_font.setWeight(QFont.Bold)
            text = item.title

            if special_feed:
                alignment = Qt.AlignTop | Qt.AlignLeft
            else:
                alignment = Qt.AlignVCenter | Qt.AlignLeft


            painter.setFont(text_font)
            text_option = QTextOption(alignment)
            text_option.setWrapMode(QTextOption.WordWrap)
            text_style_option.rect.adjust(8, 4, -4, -4)
            final_rect = QRectF(text_style_option.rect)
            text_bounding_rect = painter.boundingRect(final_rect, text, text_option)
            if text_bounding_rect.height() > final_rect.height():
                text_option.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            painter.drawText(final_rect, text, text_option)

            # draw subtitle
            if special_feed:
                subtitle = ''
                if special_feed == item.account.special_category.special_feeds['broadcast-friends']:
                    friend = item.g_item.data['via'][0]['title'].rstrip("'s shared items")
                    try:
                        subtitle = "%s (%s)" % (friend, item.normal_feeds[0].title)
                    except:
                        subtitle = "%s" % friend
                else:
                    # TODO: use something better than g_item here !!!
                    subtitle = item.g_item.origin['title'] or item.g_item.origin['url']
                    if not subtitle:
                        try:
                            subtitle = item.normal_feeds[0].title
                        except:
                            subtitle = item.g_item.feed.title or item.g_item.feed.siteUrl

                if subtitle:
                    subtitle_style_option = QStyleOptionViewItemV4(option)
                    subtitle_font = subtitle_style_option.font
                    subtitle_font.setPointSizeF(subtitle_font.pointSizeF() * 0.8)
                    subtitle_font.setWeight(QFont.Normal)
                    painter.setFont(subtitle_font)

                    palette = subtitle_style_option.palette
                    subtitle_rect = painter.boundingRect(subtitle_style_option.rect, Qt.AlignBottom | Qt.AlignRight, subtitle)
                    subtitle_rect.adjust(-8, -8, -2, -2)
                    if subtitle_rect.width() > option.rect.width() / 3:
                        # too long !
                        subtitle_rect.setX(int(2 * option.rect.width() / 3))
                    painter.setBrush(QBrush(palette.color(palette.Highlight)))
                    painter.setPen(palette.color(palette.Highlight))
                    painter.setRenderHint(QPainter.Antialiasing);
                    painter.drawRoundedRect(subtitle_rect, 4, 4);
                    subtitle_rect.adjust(4, 0, 0, 0)
                    painter.setPen(palette.color(palette.HighlightedText))
                    painter.drawText(subtitle_rect, Qt.AlignVCenter | Qt.AlignLeft, subtitle)
            
            # draw a bar for unread items
            if item.unread:
                bar_option = QStyleOptionViewItemV4(option)
                bar_option.rect.setLeft(1)
                bar_option.rect.setWidth(1)
                bar_option.rect.adjust(0, 1, 0, -1)
                palette = bar_option.palette
                painter.setPen(palette.color(palette.Highlight))
                painter.setBrush(QBrush(palette.color(palette.Highlight)))
                painter.setRenderHint(QPainter.Antialiasing);
                painter.drawRoundedRect(bar_option.rect, 4, 4);

        finally:
            painter.restore()
            
class ItemListModel(ListModel):
    def data(self, index, role):
        if index.isValid() and role == Qt.DisplayRole:
            return QVariant(self.listdata[index.row()].title)
        else:
            return QVariant()


class ItemListEventFilter(base_eventfilter_class):
    def eventFilter(self, obj, event):
        if super(ItemListEventFilter, self).eventFilter(obj, event):
            return True
        if event.type()  == QEvent.KeyPress:
            key = event.key()
            if key in (Qt.Key_A, Qt.Key_M) and \
                self.isShift(event):
                self.emit(SIGNAL("mark_all_read"))
                return True
            elif key == Qt.Key_R:
                self.emit(SIGNAL("refresh"))
                return True
            elif key == Qt.Key_F:
                self.emit(SIGNAL("fetch_more"))
                return True
            elif key == Qt.Key_U:
                self.emit(SIGNAL("toggle_unread_only"))
                return True
            elif key == Qt.Key_M:
                self.emit(SIGNAL("toggle_item_read"))
                return True
            elif key == Qt.Key_S:
                if self.isShift(event):
                    self.emit(SIGNAL("toggle_item_shared"))
                else:
                    self.emit(SIGNAL("toggle_item_starred"))
                return True
            elif key in (Qt.Key_J, Qt.Key_N):
                self.emit(SIGNAL("select_next"))
                return True
            elif key in (Qt.Key_K, Qt.Key_P):
                self.emit(SIGNAL("select_previous"))
                return True
        return QObject.eventFilter(self, obj, event)

class ItemListView(base_view_class):
    def __init__(self, controller):
        self.current_feed  = None
        self.selected_item = None

        self.unread_only_default = True
        self.show_mode_save      = True

        super(ItemListView, self).__init__(controller, self.get_ui_class(), controller.feedlist_view.win)

        self.settings_updated()

        # item list
        ilm = ItemListModel(data=[], view=self)
        ild = self.get_itemlist_delegate_class()(self.win)
        self.ui.listItemList.setModel(ilm)
        self.ui.listItemList.setItemDelegate(ild)
        self.ui.listItemList.activated.connect(self.activate_item)

    def get_ui_class(self):
        return Ui_winItemList

    def get_itemlist_delegate_class(self):
        return ItemListDelegate

    def init_menu(self):
        super(ItemListView, self).init_menu()

        # menu boutons : group for show all/updated
        self.group_show = QActionGroup(self.win)
        self.action_show_all = QAction("Show all", self.group_show)
        self.action_show_all.setCheckable(True)
        self.action_show_unread_only = QAction("Unread only", self.group_show)
        self.action_show_unread_only.setCheckable(True)
        if self.unread_only_default:
            self.action_show_unread_only.setChecked(True)
        else:
            self.action_show_all.setChecked(True)
        self.ui.menuBar.addActions(self.group_show.actions())
        self.action_show_unread_only.toggled.connect(self.trigger_unread_only)

        # other menu boutons
        self.action_refresh = QAction("Refresh", self.win)
        self.action_refresh.setObjectName('actionRefresh')
        self.ui.menuBar.addAction(self.action_refresh)
        self.action_refresh.triggered.connect(self.trigger_refresh)

        self.action_fetch_more = QAction("Fetch more", self.win)
        self.action_fetch_more.setObjectName('actionFetchMore')
        self.ui.menuBar.addAction(self.action_fetch_more)
        self.action_fetch_more.triggered.connect(self.trigger_fetch_more)

        self.action_mark_all_read = QAction("Mark all as read", self.win)
        self.action_mark_all_read.setObjectName('actionMarkAllRead')
        self.ui.menuBar.addAction(self.action_mark_all_read)
        self.action_mark_all_read.triggered.connect(self.trigger_mark_all_read)
        
        # context menu
        self.make_context_menu(self.ui.listItemList)
        
        self.action_item_read = QAction("Read", self.win)
        self.action_item_read.triggered.connect(self.trigger_item_read)
        self.action_item_read.setCheckable(True)
        self.context_menu.addAction(self.action_item_read)
        self.action_item_shared = QAction("Shared", self.win)
        self.action_item_shared.setCheckable(True)
        self.action_item_shared.triggered.connect(self.trigger_item_shared)
        self.context_menu.addAction(self.action_item_shared)
        self.action_item_starred = QAction("Starred", self.win)
        self.action_item_starred.setCheckable(True)
        self.action_item_starred.triggered.connect(self.trigger_item_starred)
        self.context_menu.addAction(self.action_item_starred)
        
        self.context_menu.addSeparator()
        self.context_menu.addAction(self.action_mark_all_read)
        self.context_menu.addAction(self.action_fetch_more)
        self.context_menu.addAction(self.action_refresh)

        self.context_menu.addSeparator()
        self.context_menu.addActions(self.group_show.actions())
                
        self.manage_actions()
        
    def init_events(self):
        super(ItemListView, self).init_events()
        
        # events
        self.add_event_filter(self.ui.listItemList, ItemListEventFilter)
        QObject.connect(self.event_filter, SIGNAL("mark_all_read"), self.trigger_mark_all_read)
        QObject.connect(self.event_filter, SIGNAL("refresh"), self.trigger_refresh)
        QObject.connect(self.event_filter, SIGNAL("fetch_more"), self.trigger_fetch_more)
        QObject.connect(self.event_filter, SIGNAL("toggle_unread_only"), self.toggle_unread_only)
        QObject.connect(self.event_filter, SIGNAL("toggle_item_read"), self.toggle_item_read)
        QObject.connect(self.event_filter, SIGNAL("toggle_item_shared"), self.toggle_item_shared)
        QObject.connect(self.event_filter, SIGNAL("toggle_item_starred"), self.toggle_item_starred)
        QObject.connect(self.event_filter, SIGNAL("select_next"), self.select_next_item)
        QObject.connect(self.event_filter, SIGNAL("select_previous"), self.select_previous_item)
        
    def manage_actions(self):
        """
        Update the menus (main menu and context menu)
        """
        # selelect item actions
        self.action_item_read.setDisabled(not self.selected_item)
        self.action_item_shared.setDisabled(not self.selected_item)
        self.action_item_starred.setDisabled(not self.selected_item)
        if self.selected_item:
            self.action_item_read.setChecked(not self.selected_item.unread)
            self.action_item_read.setDisabled(not self.selected_item.can_unread)
            self.action_item_shared.setChecked(self.selected_item.shared)
            self.action_item_starred.setChecked(self.selected_item.starred)
                
        # current feed actions
        self.action_mark_all_read.setDisabled(not (self.current_feed and self.current_feed.unread and not self.current_feed.is_loading))
        self.action_fetch_more.setDisabled(not (self.current_feed and self.can_fetch_more and not self.current_feed.is_loading))
        self.action_refresh.setDisabled(not (self.current_feed and not self.current_feed.is_loading))
        
         # display show mode
        if self.show_unread_only:
            self.action_show_unread_only.setChecked(True)
        else:
            self.action_show_all.setChecked(True)

        
    def request_context_menu(self, pos):
        """
        Called when the user ask for the context menu to be displayed
        """
        super(ItemListView, self).request_context_menu(pos)
        self.get_selected()
        self.manage_actions()
        self.display_context_menu(pos)

    @property
    def show_unread_only(self):
        """
        Return true if this feed must show only unread items
        """
        return getattr(self.current_feed, 'unread_only', self.unread_only_default)

    @property
    def can_fetch_more(self):
        return self.current_feed.can_fetch_more(self.show_unread_only)

    def trigger_unread_only(self, checked):
        """
        Action when the "unread only" button is checked or unchecked
        """
        if self.show_unread_only != checked:
            self.get_selected()
            self.current_feed.unread_only = checked
            self.update_item_list()
        
    def toggle_unread_only(self):
        """
        Called when we want to toggle the display between all items or only 
        unread ones
        """
        self.action_show_unread_only.setChecked(not self.show_unread_only)
        
    def get_selected(self, item=None):
        """
        Save the current selected item for select it back when the list will
        be refreshed
        """
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
        """
        Try to restore the selected item in the list
        """
        if item is None:
            item = self.selected_item
        else:
            self.selected_item = item
        if item:
            index = self.ui.listItemList.model().index_of(item)
            if index:
                self.ui.listItemList.setCurrentIndex(index)
        
    def trigger_refresh(self):
        """
        Called when the refresh button is called
        """
        self.get_selected()
        self.manage_loading(loading=True)
        self.current_feed.fetch_content(unread_only=self.show_unread_only)
        self.manage_actions()
            
    def trigger_fetch_more(self):
        """
        Called when the "fetch more" button is called
        """
        self.get_selected()
        self.manage_loading(loading=True)
        self.current_feed.fetch_more_content(unread_only=self.show_unread_only)
        self.manage_actions()
        
    def set_current_feed(self, feed):
        """
        Set the current item as the on selected in the list
        """
        self.update_listview(content=[])
        self.current_feed = feed
        self.manage_loading()
        self.update_title()
        self.ui.listItemList.setFocus(Qt.OtherFocusReason)
        self.update_item_list()
        self.select_row(row=0)
        self.get_selected()
        self.manage_actions()
        return True
                
    def select_row(self, row=None, item=None):
        """
        Try to select an item in the list, by a specific item, or by a number
        """
        try:
            index = None
            model = self.ui.listItemList.model()
            if item:
                index = model.index_of(item)
            if not index:
                if not row:
                    row = 0
                index = model.index(row)
            self.ui.listItemList.setCurrentIndex(index)
        except:
            pass
        
    def manage_loading(self, loading=None):
        """
        Manage the loading indicator
        """
        if loading is None:
            loading = False
        if not loading:
            if not self.current_feed:
                loading = True
            else:
                if self.current_feed.is_loading:
                    loading = True
                else:
                    for category in self.current_feed.categories:
                        if category.category_feed and category.category_feed.is_loading:
                            loading = True
                            break
        if loading:
            self.start_loading()
        else:
            self.stop_loading()
        
    def get_title(self):
        """
        Get the title for this view : the feed title and the unread count
        """
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
        self.update_listview(content=self.current_feed.get_items(unread_only=self.show_unread_only))
        self.set_selected()
        self.action_fetch_more.setDisabled(not self.can_fetch_more)
        
    def feed_content_fetching_started(self, feed):
        """
        Called when a feed content fetching operation begins
        """
        if not self.current_feed:
            return
        if isinstance(feed, CategoryFeed):
            if self.current_feed not in feed.categories[0].feeds:
                return
        elif feed != self.current_feed:
            return
        self.manage_loading(loading=True)
        self.manage_actions()
        
    def feed_content_fetched(self, feed):
        """
        Called when a feed content was just fetched, to redraw the ui
        """
        if not self.current_feed:
            return
        if isinstance(feed, CategoryFeed):
            if self.current_feed not in feed.categories[0].feeds:
                return
        elif feed != self.current_feed:
            return
        self.get_selected()
        self.update_item_list()
        self.manage_loading()
        self.manage_actions()

    def update_listview(self, content=[]):
        """
        Update the list with feed's items
        """
        old_model = self.ui.listItemList.model()
        model = ItemListModel(data=content, view=self)
        self.ui.listItemList.setModel(model)
        del old_model
        
    def activate_item(self, index):
        """
        Called when the list in clicked, to display the item selected
        """
        item = index.model().listdata[index.row()]
        self.get_selected(item)
        self.controller.display_item(item)
        
    def select_next_item(self):
        """
        Select the next item in the list (but without activating it)
        Return True if the operation is successfull
        """
        self.get_selected()
        item = self.ui.listItemList.model().get_next(self.selected_item)
        if item:
            self.set_selected(item)
            return not not self.selected_item
        return False
        
    def activate_next_item(self):
        """
        Activate the item just after the current one in the list.
        Usefull for keyboard shortcuts
        """
        select_ok = self.select_next_item()
        if select_ok:
            self.controller.display_item(self.selected_item)
        else:
            if self.can_fetch_more:
                self.controller.display_message("No more message, please fetch more !")
            else:
                self.controller.display_message("No more message !")
                
    def select_previous_item(self):
        """
        Select the previous item in the list (but without activating it)
        Return True if the operation is successfull
        """
        self.get_selected()
        item = self.ui.listItemList.model().get_previous(self.selected_item)
        if item:
            self.set_selected(item)
            return not not self.selected_item
        return False

    def activate_previous_item(self):
        """
        Activate the item just before the current one in the list.
        Usefull for keyboard shortcuts
        """
        select_ok = self.select_previous_item()
        if select_ok:
            self.controller.display_item(self.selected_item)
        else:
            self.controller.display_message("No more message, you're at the top of the list")
        
    def settings_updated(self):
        """
        Called when settings are updated
        """
        super(ItemListView,  self).settings_updated()
        show_mode = str(settings.get('items', 'show_mode'))
        self.unread_only_default = show_mode.find('unread') != -1
        self.show_mode_save      = show_mode.find('nosave') == -1

    def update_item(self, item):
        """
        Called when a category is updated, to refresh it's entry in the list, 
        and it's category_feed if it has one
        """
        try:
            index = self.ui.listItemList.model().index_of(item)
            # TODO: missing a way to insert row, don't know how to add data with insertRows
            # see https://svn.enthought.com/svn/enthought/TraitsBackendQt/trunk/enthought/traits/ui/qt4/list_str_model.py
            #if item.isRead() and self.show_updated_only():
            #    self.ui.listItemList.model().removeRow(index.row())
            #else:
            self.ui.listItemList.update(index)
        except:
            pass
        self.update_title()

    def trigger_mark_all_read(self):
        """
        Called when the button "mark all as read" is activated
        """
        self.current_feed.mark_as_read()
        self.controller.feed_read(self.current_feed)
        
    def feed_read(self, feed):
        """
        Visually update all the items in the list
        """
        if feed != self.current_feed:
            return
        self.action_mark_all_read.setDisabled(True)
        for item in self.current_feed.get_items():
            self.update_item(item)
        
    def item_read(self, item):
        """
        Called when an item the unread/read status of an item is changed, to 
        visually update it in the list
        """
        self.update_item(item)
        
    def item_shared(self, item):
        """
        Called when an item the shared status of an item is changed, to 
        visually update it in the list
        """
        self.update_item(item)
        
    def item_starred(self, item):
        """
        Called when an item the starred status of an item is changed, to 
        visually update it in the list
        """
        self.update_item(item)
        
    def trigger_item_read(self, checked):
        """
        Mark the selected item as read (checked==True) or unread
        """
        if self.selected_item and checked == self.selected_item.unread:
            if self.selected_item.unread:
                self.selected_item.mark_as_read()
            else:
                self.selected_item.mark_as_unread()
            self.controller.item_read(self.selected_item)
        
    def trigger_item_shared(self, checked):
        """
        Share the selected item (checked==True) or unshare it
        """
        if self.selected_item and checked != self.selected_item.shared:
            if self.selected_item.shared:
                self.selected_item.unshare()
            else:
                self.selected_item.share()
            self.controller.item_shared(self.selected_item)
        
    def trigger_item_starred(self, checked):
        """
        Share the selected item (checked==True) or unshare it
        """
        if self.selected_item and checked != self.selected_item.starred:
            if self.selected_item.starred:
                self.selected_item.unstar()
            else:
                self.selected_item.star()
            self.controller.item_starred(self.selected_item)
        
    def toggle_item_read(self):
        """
        Called when we want to toggle the read/unread status of the selected item
        """
        self.get_selected()
        if not self.selected_item:
            return
        was_unread = self.selected_item.unread
        message = 'Entry now marked as unread'
        if was_unread:
            message = 'Entry now marked as read'
        self.trigger_item_read(was_unread)
        self.display_message(message)
        
    def toggle_item_shared(self):
        """
        Called when we want to toggle the shared status of the selected item
        """
        self.get_selected()
        if not self.selected_item:
            return
        was_shared = self.selected_item.shared
        message = 'Shared flag is now ON'
        if was_shared:
            message = 'Shared flag is now OFF'
        self.trigger_item_shared(not was_shared)
        self.controller.display_message(message)

    def toggle_item_starred(self):
        """
        Called when we want to toggle the starred status of the selected item
        """
        self.get_selected()
        if not self.selected_item:
            return
        was_starred = self.selected_item.starred
        message = 'Starred flag is now ON'
        if was_starred:
            message = 'Starred flag is now OFF'
        self.trigger_item_starred(not was_starred)
        self.controller.display_message(message)
