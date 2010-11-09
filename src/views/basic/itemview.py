# -*- coding: utf-8 -*-

"""
Item content view
"""
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtWebKit import *

import sys
    
from ui.Ui_itemview import Ui_winItemView
from . import View, ViewEventFilter, base_view_class, base_eventfilter_class
from utils.toolbar import ToolbarManager, Toolbar

from engine import settings, log
from engine.models import *


class ItemViewEventFilter(base_eventfilter_class):
    def eventFilter(self, obj, event):
        if super(ItemViewEventFilter, self).eventFilter(obj, event):
            return True
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
            elif key == Qt.Key_M:
                self.emit(SIGNAL("toggle_read"))
                return True
            elif key == Qt.Key_V:
                if self.isShift(event):
                    self.emit(SIGNAL("view_original_gread"))
                else:
                    self.emit(SIGNAL("view_original_browser"))
                return True
            elif key == Qt.Key_S:
                if self.isShift(event):
                    self.emit(SIGNAL("toggle_shared"))
                else:
                    self.emit(SIGNAL("toggle_starred"))
                return True
        if self.postEventFilter(obj, event):
            return True
        return QObject.eventFilter(self, obj, event)

class WebPage(QWebPage):
    def __init__(self, *args, **kwargs):
        super(WebPage, self).__init__(*args, **kwargs)
        self.user_agent = settings.get('content', 'user_agent')
        
    def userAgentForUrl(self, url):
        if not self.user_agent:
            self.user_agent = super(WebPage, self).userAgentForUrl(url)
        return self.user_agent

class ItemViewView(base_view_class):
    def __init__(self, controller):
        # item displayed
        self.current_item = None
        self.current_page_is_content = False
        
        super(ItemViewView, self).__init__(controller, self.get_ui_class(), controller.itemlist_view.win)
        
        # web view
        self.ui.webView.setPage(WebPage(parent=self.ui.webView))
        self.ui.webView.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        self.ui.webView.page().linkClicked.connect(self.link_clicked)
        self.ui.webView.loadFinished.connect(self.trigger_web_view_loaded)
        self.default_zoom_factor = self.ui.webView.zoomFactor()
        self.ui.webView.setZoomFactor(self.default_zoom_factor*int(settings.get('content', 'zoom_factor'))/100)
        self.current_zoom_factor = self.ui.webView.zoomFactor()
        self.ui.webView.setStyleSheet('background: white')

        self.init_toolbars()

    def get_ui_class(self):
        return Ui_winItemView

    def init_toolbars(self):
        toolbar_class = self.get_toolbar_class()
        self.leftToolbar = toolbar_class('<', 'Previous item', self.show_previous, 0, 0.7, parent=self.win)
        self.rightToolbar = toolbar_class('>', 'Next item', self.show_next, 1, 0.7, parent=self.win)
        self.toolbar_manager = self.get_toolbar_manager_class()([self.leftToolbar, self.rightToolbar], event_target=self.ui.webView.page(), parent=self.win)
        
    def get_toolbar_class(self):
        return Toolbar
        
    def get_toolbar_manager_class(self):
        return ToolbarManager

    def init_menu(self):
        super(ItemViewView, self).init_menu()
        
        menu_container = self.get_menu_container()

        self.group_actions = QActionGroup(self.win)
        self.group_actions.setExclusive(False)
        # menu bar : read/unread
        self.action_read = QAction("Read", self.group_actions)
        self.action_read.setObjectName('actionRead')
        self.action_read.setCheckable(True)
        self.action_read.triggered.connect(self.trigger_read)
        # menu bar : starred
        self.action_starred = QAction("Starred", self.group_actions)
        self.action_starred.setObjectName('actionStarred')
        self.action_starred.setCheckable(True)
        self.action_starred.triggered.connect(self.trigger_starred)
        # menu bar : shared
        self.action_shared = QAction("Shared", self.group_actions)
        self.action_shared.setObjectName('actionShared')
        self.action_shared.setCheckable(True)
        self.action_shared.triggered.connect(self.trigger_shared)
        
        menu_container.addActions(self.group_actions.actions())

        menu_container.addSeparator()

        # menu bar : see original
        self.group_view = QActionGroup(self.win)
        self.group_actions.setExclusive(False)
        self.action_view_original_browser = QAction("View original in Browser", self.group_view)
        self.action_view_original_browser.setObjectName('actionViewOriginalBrowser')
        self.action_view_original_browser.triggered.connect(self.trigger_view_original_browser)
        self.action_view_original_gread = QAction("View original in GRead", self.group_view)
        self.action_view_original_gread.setObjectName('actionViewOriginalGRead')
        self.action_view_original_gread.triggered.connect(self.trigger_view_original_gread)
        # menu bar : return to item
        self.action_return_to_item = QAction("Return to entry", self.group_view)
        self.action_return_to_item.setObjectName('actionReturnToItem')
        self.action_return_to_item.triggered.connect(self.trigger_return_to_item)

        menu_container.addActions(self.group_view.actions())

        # context menu
        self.make_context_menu(self.ui.webView)
        self.context_menu.addActions(self.group_actions.actions())
        self.context_menu.addSeparator()
        self.context_menu.addActions(self.group_view.actions())
        self.context_menu.addSeparator()
        for web_action in (QWebPage.Copy, QWebPage.Back, QWebPage.Reload, QWebPage.Stop, QWebPage.CopyLinkToClipboard, \
            ):#QWebPage.OpenImageInNewWindow, QWebPage.DownloadImageToDisk):
            self.context_menu.addAction(self.ui.webView.pageAction(web_action))
            
    def get_event_filter_class(self):
        return ItemViewEventFilter
        
    def init_events(self):
        self.add_event_filter(self.ui.webView, self.get_event_filter_class())
        super(ItemViewView, self).init_events()
        QObject.connect(self.event_filter, SIGNAL("zoom"), self.zoom)
        QObject.connect(self.event_filter, SIGNAL("next"), self.show_next)
        QObject.connect(self.event_filter, SIGNAL("previous"), self.show_previous)
        QObject.connect(self.event_filter, SIGNAL("toggle_read"), self.toggle_read)
        QObject.connect(self.event_filter, SIGNAL("toggle_shared"), self.toggle_shared)
        QObject.connect(self.event_filter, SIGNAL("toggle_starred"), self.toggle_starred)
        QObject.connect(self.event_filter, SIGNAL("view_original_gread"), self.trigger_view_original_gread)
        QObject.connect(self.event_filter, SIGNAL("view_original_browser"), self.trigger_view_original_browser)

    def manage_actions(self):
        """
        Update the menus (main menu and context menu)
        """
        if self.current_item:
            self.action_read.setChecked(not self.current_item.unread)
            self.action_read.setDisabled(not self.current_item.can_unread)
            self.action_shared.setChecked(self.current_item.shared)
            self.action_starred.setChecked(self.current_item.starred)
                
            if self.current_page_is_content:
                self.action_view_original_gread.setDisabled(self.current_item.url is None)
                self.action_view_original_browser.setDisabled(self.current_item.url is None)
                self.action_return_to_item.setDisabled(True)
                self.action_return_to_item.setVisible(False)
            else:
                self.action_return_to_item.setVisible(True)
                self.action_return_to_item.setDisabled(False)

        
    def request_context_menu(self, pos):
        """
        Called when the user ask for the context menu to be displayed
        """
        super(ItemViewView, self).request_context_menu(pos)
        self.manage_actions()
        self.display_context_menu(pos)

    def set_current_item(self, item):
        """
        Display the specified item it the view
        """
        try:
            self.start_loading()
    
            self.current_item = item
            self.update_title()
           
            # mark the item as read
            if item.unread:
                self.trigger_read(True)
                
            # display content
            self.current_page_is_content = True
            self.ui.webView.stop()
            self.ui.webView.setHtml("")
            self.ui.webView.setHtml(item.content)
            self.ui.webView.setZoomFactor(self.current_zoom_factor)
    
            self.ui.webView.setFocus(Qt.OtherFocusReason)
            
            # toolbars
            previous = self.controller.get_previous_item()
            next     = self.controller.get_next_item()
            if previous:
                self.leftToolbar.set_tooltip(previous.title)
                self.leftToolbar.enable()
            else:
                self.leftToolbar.disable()
            if next:
                self.rightToolbar.set_tooltip(next.title)
                self.rightToolbar.enable()
            else:
                self.rightToolbar.disable()
            self.toolbar_manager.display()

            # menus
            self.action_read.setChecked(not item.unread)
            self.action_read.setDisabled(not item.can_unread)
            self.action_shared.setChecked(item.shared)
            self.action_starred.setChecked(item.starred)
            
            self.manage_actions()
            

            str = "%s - " % item.title
            statuses = []
            if item.unread:
                statuses.append('unread')
            else:
                statuses.append('read')
            if item.shared:
                statuses.append('shared')
            if item.starred:
                statuses.append('starred')
            self.display_banner("%s [%s]" % (item.title, ', '.join(statuses)))

        
        except Exception, e:
            log("ERROR WHILE DISPLAYING ITEM : %s" % e)
            return False
        else:
            return True
                
    def trigger_read(self, checked):
        """
        Mark the item as read (checked==True) or unread
        """
        if checked == self.current_item.unread:
            if self.current_item.unread:
                self.current_item.mark_as_read()
            else:
                self.current_item.mark_as_unread()
            self.controller.item_read(self.current_item)

    def trigger_shared(self, checked):
        """
        Share the item (checked==True) or unshare it
        """
        if checked != self.current_item.shared:
            if self.current_item.shared:
                self.current_item.unshare()
            else:
                self.current_item.share()
            self.controller.item_shared(self.current_item)

    def trigger_starred(self, checked):
        """
        Star the item (checked==True) or unstar id
        """
        if checked != self.current_item.starred:
            if self.current_item.starred:
                self.current_item.unstar()
            else:
                self.current_item.star()
            self.controller.item_starred(self.current_item)
        
    def trigger_view_original_gread(self):
        """
        Display the original item's url in the internal browser
        """
        self.open_url(QUrl(self.current_item.url), force_in_gread=True)

    def trigger_view_original_browser(self):
        """
        Display the original item's url in the real browser
        """
        self.open_url(QUrl(self.current_item.url))

    def trigger_return_to_item(self):
        """
        When the internal browser is used for other thant the original feed
        content, a "return to item" button is added to call this method, which
        will display the original item's content
        """
        self.manage_actions()
        self.current_page_is_content = True
        self.ui.webView.setHtml(self.current_item.content)

    def open_url(self, url, force_in_gread=False):
        """
        Ask for opening a url, in the internal browser if force_in_gread is
        True, else in the real browser. If the real browser cannot be opened,
        the url is opened in the internal browser
        """
        if force_in_gread or not QDesktopServices.openUrl(url):
            self.ui.webView.stop()
            self.current_page_is_content = False
            self.ui.webView.setHtml("")
            self.start_loading()
            self.manage_actions()
            self.ui.webView.setZoomFactor(self.current_zoom_factor)
            self.ui.webView.load(url)
            return False
        return True
        
    def link_clicked(self, url):
        """
        Called when a link is clicked in the web view. Then try to open
        this link in the real browser
        """
        self.open_url(url)
                        
    def get_title(self):
        """
        Return the current item's title
        """
        title = ""
        if self.current_item:
            if settings.get('content', 'feed_in_title'):
                try:
                    title = self.current_item.normal_feeds[0].title\
                        or self.current_item.g_item.origin['title']\
                        or self.current_item.g_item.origin['url']
                except:
                    pass
            if not title:
                title = self.current_item.title
        return title

    def settings_updated(self):
        """
        Called when settings are updated
        """
        self.ui.webView.setZoomFactor(self.default_zoom_factor*int(settings.get('content', 'zoom_factor'))/100)
        self.current_zoom_factor = self.ui.webView.zoomFactor()
        self.ui.webView.page().user_agent = settings.get('content', 'user_agent')
        
    def zoom(self, zoom_in=True):
        """
        Apply a 1.2 factor to the current zoom level if zoom_in is True, or
        1/1.2 if it's False
        """
        factor = 1.2
        if not zoom_in:
            factor = 1/1.2
        self.ui.webView.setZoomFactor(self.ui.webView.zoomFactor()*factor)

    def trigger_web_view_loaded(self, ok):
        """
        Called when a content is fully loaded in the web view, to stop the
        loading animation
        """
        self.stop_loading()
        
    def show_next(self):
        """
        Ask for controller to display the next available item
        """
        self.controller.display_next_item()
        
    def show_previous(self):
        """
        Ask for controller to display the previous available item
        """
        self.controller.display_previous_item()
        
    def toggle_read(self):
        """
        Called when we want to toggle the read/unread status of the current item
        """
        was_unread = self.current_item.unread
        message = 'Entry now marked as unread'
        if was_unread:
            message = 'Entry now marked as read'
        self.trigger_read(was_unread)
        self.action_read.setChecked(was_unread)
        self.display_message(message)
        
    def toggle_shared(self):
        """
        Called when we want to toggle the shared status of the current item
        """
        was_shared = self.current_item.shared
        message = 'Shared flag is now ON'
        if was_shared:
            message = 'Shared flag is now OFF'
        self.trigger_shared(not was_shared)
        self.action_shared.setChecked(not was_shared)
        self.controller.display_message(message)

    def toggle_starred(self):
        """
        Called when we want to toggle the starred status of the current item
        """
        was_starred = self.current_item.starred
        message = 'Starred flag is now ON'
        if was_starred:
            message = 'Starred flag is now OFF'
        self.trigger_starred(not was_starred)
        self.action_starred.setChecked(not was_starred)
        self.controller.display_message(message)

    def help_keys(self):
        return {
            'title': 'Item view', 
            'keys': [
                ('Back/Esc', 'Return to items list'), 
                ('F7/F8', 'Zoom in/out'), 
                ('J/N', 'Move to next item'), 
                ('K/P', 'Move to previous item'), 
                ('M', 'Toggle read status'), 
                ('S', 'Toggle starred status'), 
                ('shift-S', 'Toggle shared status'), 
                ('V', 'Show original in external browser'), 
                ('shift-V', 'Show original in GRead'), 
            ]
       }

        
    def item_read(self, item):
        """
        Called when an item the unread/read status of an item is changed, to 
        visually update it in the list
        """
        self.manage_actions()
        
    def item_shared(self, item):
        """
        Called when an item the shared status of an item is changed, to 
        visually update it in the list
        """
        self.manage_actions()
        
    def item_starred(self, item):
        """
        Called when an item the starred status of an item is changed, to 
        visually update it in the list
        """
        self.manage_actions()
