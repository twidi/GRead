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

from engine import settings
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
            elif key in (Qt.Key_Down, Qt.Key_Up, Qt.Key_Left, Qt.Key_Right, Qt.Key_Space):
                self.emit(SIGNAL("init_browser_scrollbars"))
                return False
        return QObject.eventFilter(self, obj, event)

class ItemViewView(base_view_class):
    def __init__(self, controller):
        # item displayed
        self.current_item = None
        self.current_page_is_content = False
        
        super(ItemViewView, self).__init__(controller, self.get_ui_class(), controller.itemlist_view.win)
        
        # web view
        self.ui.webView.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        self.ui.webView.page().linkClicked.connect(self.link_clicked)
        self.ui.webView.loadFinished.connect(self.trigger_web_view_loaded)

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
        # menu bar : read/unread
        self.action_read = QAction("Read", self.win)
        self.action_read.setObjectName('actionRead')
        self.ui.menuBar.addAction(self.action_read)
        self.action_read.setCheckable(True)
        self.action_read.triggered.connect(self.trigger_read)
        # menu bar : see original
        self.action_view_original_browser = QAction("View original in Browser", self.win)
        self.action_view_original_browser.setObjectName('actionViewOriginalBrowser')
        self.ui.menuBar.addAction(self.action_view_original_browser)
        self.action_view_original_browser.triggered.connect(self.trigger_view_original_browser)
        self.action_view_original_gread = QAction("View original in GRead", self.win)
        self.action_view_original_gread.setObjectName('actionViewOriginalGRead')
        self.ui.menuBar.addAction(self.action_view_original_gread)
        self.action_view_original_gread.triggered.connect(self.trigger_view_original_gread)
        # menu bar : return to item
        self.action_return_to_item = QAction("Return to entry", self.win)
        self.action_return_to_item.setObjectName('actionReturnToItem')
        self.ui.menuBar.addAction(self.action_return_to_item)
        self.action_return_to_item.triggered.connect(self.trigger_return_to_item)

        # context menu
        self.make_context_menu(self.ui.webView)
        self.context_menu.addAction(self.action_read)
        self.context_menu.addAction(self.action_shared)
        self.context_menu.addAction(self.action_starred)
        self.context_menu.addSeparator()
        self.context_menu.addAction(self.action_view_original_browser)
        self.context_menu.addAction(self.action_view_original_gread)
        self.context_menu.addAction(self.action_return_to_item)
        self.context_menu.addSeparator()
        for web_action in (QWebPage.Copy, QWebPage.Back, QWebPage.Reload, QWebPage.Stop, QWebPage.CopyLinkToClipboard, \
            ):#QWebPage.OpenImageInNewWindow, QWebPage.DownloadImageToDisk):
            self.context_menu.addAction(self.ui.webView.pageAction(web_action))
        
    def init_events(self):
        super(ItemViewView, self).init_events()
        
        # events
        self.add_event_filter(self.win, ItemViewEventFilter)
        QObject.connect(self.event_filter, SIGNAL("zoom"), self.zoom)
        QObject.connect(self.event_filter, SIGNAL("next"), self.show_next)
        QObject.connect(self.event_filter, SIGNAL("previous"), self.show_previous)
        QObject.connect(self.event_filter, SIGNAL("toggle_read"), self.toggle_read)
        QObject.connect(self.event_filter, SIGNAL("toggle_shared"), self.toggle_shared)
        QObject.connect(self.event_filter, SIGNAL("toggle_starred"), self.toggle_starred)
        QObject.connect(self.event_filter, SIGNAL("view_original_gread"), self.trigger_view_original_gread)
        QObject.connect(self.event_filter, SIGNAL("view_original_browser"), self.trigger_view_original_browser)
        QObject.connect(self.event_filter, SIGNAL("init_browser_scrollbars"), self.init_browser_scrollbars)

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
        self.start_loading()

        self.current_item = item
        self.update_title()
        
        # mark the item as read
        if item.unread:
            self.trigger_read(True)
            
        # display content
        self.current_page_is_content = True
        self.ui.webView.setHtml(item.content)

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
        self.open_url(QUrl(self.current_item.url), force_in_gread=True, zoom_gread=1.0)

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

    def open_url(self, url, force_in_gread=False, zoom_gread=None):
        """
        Ask for opening a url, in the internal browser if force_in_gread is
        True, else in the real browser. If the real browser cannot be opened,
        the url is opened in the internal browser
        """
        if force_in_gread or not QDesktopServices.openUrl(url):
            self.current_page_is_content = False
            self.ui.webView.setHtml("")
            self.start_loading()
            self.manage_actions()
            if zoom_gread is not None:
                self.ui.webView.setZoomFactor(zoom_gread)
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
            title = self.current_item.title
        return title

    def zoom(self, zoom_in=True):
        """
        Apply a 1.1 factor to the current zoom level if zoom_in is True, or
        1/1.1 if it's False
        """
        factor = 1.1
        if not zoom_in:
            factor = 1/1.1
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
        
    def init_browser_scrollbars(self):
        """
        We need scrollbars !
        """
        frame = self.ui.webView.page().currentFrame()
        if frame.scrollBarPolicy(Qt.Vertical) != Qt.ScrollBarAsNeeded:
            frame.setScrollBarPolicy(Qt.Vertical, Qt.ScrollBarAsNeeded)
