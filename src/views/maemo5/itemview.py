# -*- coding: utf-8 -*-

"""
Feed list view
"""
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtWebKit import *

import sys
    
from views.maemo5.utils.qwebviewselectionsuppressor import QWebViewSelectionSuppressor
from views.maemo5.ui.Ui_itemview import Ui_winItemView
from views.maemo5 import MAEMO5_PRESENT, MAEMO5_ZOOMKEYS, View
from views.maemo5.utils.toolbar import ToolbarManager, Toolbar

if MAEMO5_PRESENT:
    try:
        from views.maemo5.utils.zoomkeys import grab as grab_zoom_keys
        MAEMO5_ZOOMKEYS = True
    except Exception, e:
        sys.stderr.write("ZOOMKEYS ERROR : %s" % e)

from engine import settings
from engine.models import *


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
            elif key == Qt.Key_M:
                self.emit(SIGNAL("toggle_read"))
                return True
            elif key == Qt.Key_V:
                if event.modifiers() & Qt.ShiftModifier:
                    self.emit(SIGNAL("view_original_gread"))
                else:
                    self.emit(SIGNAL("view_original_browser"))
                return True
            elif key == Qt.Key_S:
                if event.modifiers() & Qt.ShiftModifier:
                    self.emit(SIGNAL("toggle_shared"))
                else:
                    self.emit(SIGNAL("toggle_starred"))
                    
                return True
        return QObject.eventFilter(self, obj, event)

class ItemViewView(View):
    def __init__(self, controller):
        super(ItemViewView, self).__init__(controller, Ui_winItemView, controller.itemlist_view.win)
        
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

        # menu bar

        self.add_orientation_menu()

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

        # toolbars
        self.leftToolbar = Toolbar('<', 'Previous item', self.show_previous, 0, 0.7, parent=self.win)
        self.rightToolbar = Toolbar('>', 'Next item', self.show_next, 1, 0.7, parent=self.win)
        self.toolbar_manager = ToolbarManager([self.leftToolbar, self.rightToolbar], event_target=self.ui.webView.page(), parent=self.win)
        
        # events
        self.eventFilter = ItemViewEventFilter(self.win)
        self.win.installEventFilter(self.eventFilter)
        QObject.connect(self.eventFilter, SIGNAL("zoom"), self.zoom)
        QObject.connect(self.eventFilter, SIGNAL("next"), self.show_next)
        QObject.connect(self.eventFilter, SIGNAL("previous"), self.show_previous)
        QObject.connect(self.eventFilter, SIGNAL("toggle_read"), self.toggle_read)
        QObject.connect(self.eventFilter, SIGNAL("toggle_shared"), self.toggle_shared)
        QObject.connect(self.eventFilter, SIGNAL("toggle_starred"), self.toggle_starred)
        QObject.connect(self.eventFilter, SIGNAL("view_original_gread"), self.trigger_view_original_gread)
        QObject.connect(self.eventFilter, SIGNAL("view_original_browser"), self.trigger_view_original_browser)

        # item displayed
        self.current_item = None

    def set_current_item(self, item):
        """
        Display the specified item it the view
        """
        self.start_loading()

        self.leftToolbar.enable()
        self.rightToolbar.enable()
        self.toolbar_manager.display()

        self.current_item = item
        self.update_title()
        
        # mark the item as read
        if item.unread:
            self.trigger_mark_read(True)

        # menus
        self.action_mark_read.setChecked(not item.unread)
        self.action_mark_read.setDisabled(not item.can_unread)
        self.action_shared.setChecked(item.shared)
        self.action_starred.setChecked(item.starred)
            
        self.action_view_original_gread.setDisabled(item.url is None)
        self.action_view_original_gread.setVisible(True)
        self.action_view_original_browser.setDisabled(item.url is None)
        self.action_view_original_browser.setVisible(True)
        self.action_return_to_item.setDisabled(True)
        self.action_return_to_item.setVisible(False)
            
        # display content
        if MAEMO5_PRESENT:
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
            self.display_message_box("%s [%s]" % (item.title, ', '.join(statuses)))
        self.ui.webView.setHtml(item.content)

        self.ui.webView.setFocus(Qt.OtherFocusReason)
        return True

    def trigger_mark_read(self, checked):
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
        self.action_view_original_gread.setDisabled(False)
        self.action_view_original_gread.setVisible(True)
        self.action_return_to_item.setDisabled(True)
        self.action_return_to_item.setVisible(False)
        self.ui.webView.setHtml(self.current_item.content)

    def open_url(self, url, force_in_gread=False, zoom_gread=None):
        """
        Ask for opening a url, in the internal browser if force_in_gread is
        True, else in the real browser. If the real browser cannot be opened,
        the url is opened in the internal browser
        """
        if force_in_gread or not QDesktopServices.openUrl(url):
            self.ui.webView.setHtml("")
            self.start_loading()
            self.action_view_original_gread.setDisabled(True)
            self.action_view_original_gread.setVisible(False)
            self.action_return_to_item.setDisabled(False)
            self.action_return_to_item.setVisible(True)
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
        self.trigger_mark_read(was_unread)
        self.action_mark_read.setChecked(was_unread)
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
