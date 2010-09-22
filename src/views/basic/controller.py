# -*- coding: utf-8 -*-

"""
GRead controller
"""
from PyQt4.QtCore import QObject, Qt, QTimer, SIGNAL
from PyQt4.QtGui import QApplication

from engine.signals import SIGNALS
from engine.models import *
from engine.operations import Operation
from feedlist import FeedListView
from itemlist import ItemListView
from itemview import ItemViewView
from settings_dialog import SettingsDialog

class Controller(QObject):

    def __init__(self):
        """
        Create the Controller, inialize all things (settings, signals...)
        """
        super(Controller, self).__init__(parent=None)
        
        self.is_running = False
        
        # the current Google Reader account
        self.account = Account()

        # views
        self.views = []
        self.current_view = None

        # connect signals
        QObject.connect(self, SIGNALS["settings_updated"], self.settings_updated)
        QObject.connect(self.account.operations_manager, SIGNALS["operation_started"], self.update_titles, Qt.QueuedConnection)
        QObject.connect(self.account.operations_manager, SIGNALS["operation_ended"], self.update_titles, Qt.QueuedConnection)
        QObject.connect(self.account.operations_manager, SIGNALS["get_account_feeds_started"], self.feeds_fetching_started, Qt.QueuedConnection)
        QObject.connect(self.account.operations_manager, SIGNALS["get_account_feeds_done"], self.feeds_fetched, Qt.QueuedConnection)
        QObject.connect(self.account.operations_manager, SIGNALS["get_feed_content_started"], self.feed_content_fetching_started, Qt.QueuedConnection)
        QObject.connect(self.account.operations_manager, SIGNALS["get_more_feed_content_started"], self.feed_content_fetching_started, Qt.QueuedConnection)
        QObject.connect(self.account.operations_manager, SIGNALS["get_feed_content_done"], self.feed_content_fetched, Qt.QueuedConnection)
        QObject.connect(self.account.operations_manager, SIGNALS["get_more_feed_content_done"], self.feed_content_fetched, Qt.QueuedConnection)
        
    def create_views(self):
        """
        Create all the views used by the application
        """
        self.settings_dialog = SettingsDialog(controller=self)
        self.feedlist_view   = FeedListView(controller=self)
        self.itemlist_view   = ItemListView(controller=self)
        self.itemview_view   = ItemViewView(controller=self)
        
    def run(self):
        """
        Initialize graphic things and show the application by displaying the 
        feed list window
        """
        if self.is_running:
            return
        self.is_running = True
        
        self.create_views()
        self.current_view = self.feedlist_view
        
        self.current_view.show(app_just_launched=True)
        
    def settings_updated(self, auth_unverified_changed=False):
        """
        When settings are updated, call same method for all views, and if 
        the auth_unverified_changed parameter is true, ask for a resync
        """
        for view in self.views:
            try:
                view.settings_updated()
            except:
                pass
        if auth_unverified_changed:
            self.account.fetch_feeds(fetch_unread_content=True)
        
    def add_view(self, view):
        """
        Add a view to the list of manages views
        """
        self.views.append(view)
        
    def get_title_operations_part(self):
        """
        Get the part of the title which will handle the running operations counter
        """
        nb = self.account.operations_manager.count_running()
        if nb:
            return "%d operations" % nb
        else:
            return ""
            
    def update_titles(self):
        """
        Update titles for all views
        """
        for view in self.views:
            try:
                view.update_title()
            except:
                pass
            
    def timeout_title_timer(self):
        """
        Called when the title timer delay is done
        """
        if self.current_view:
            self.current_view.update_display_title()

    def hide_children(self, view):
        """
        Hide all views which are children of the specified one
        """
        for child in self.views:
            if child.win.parent() == view.win and child.win.isVisible():
                self.hide_children(child)
                child.win.hide()

    def set_current_view(self, view):
        """
        Set the specified view as the current one
        """
        if view != self.current_view:
            old_current_view  = self.current_view
            self.current_view = view
            self.hide_children(self.current_view)
            self.current_view.show()

    def is_current_view(self, view):
        return view == self.current_view
        
    def switch_view(self, name):
        """
        Swith to the a view specified by its name
        """
        if name == 'feedlist':
            view = self.feedlist_view
        elif name == 'itemlist':
            view = self.itemlist_view
        elif name == 'itemview':
            view = self.itemview_view
        else:
            return
        self.set_current_view(view)
        
    def display_message(self, message, level="information"):
        """
        Display a message for the current view
        """
        if self.current_view:
            self.current_view.display_message(message, level)
        
    def display_feed(self, feed):
        """
        Display a feed by displaying the itemlist view.
        If the specified feed cannot be selected, return to the previous view
        """
        self.switch_view('itemlist')
        if not self.itemlist_view.set_current_feed(feed):
            self.switch_view('feedlist')
        
    def trigger_settings(self):
        """
        Will display the settings dialog box
        """
        self.settings_dialog.open()
        
    def start_loading(self):
        """
        Activate the loading indicator in the current view
        """
        if self.current_view:
            self.current_view.start_loading()
            
    def stop_loading(self):
        """
        Stop the loading indicator in the current view
        """
        if self.current_view:
            self.current_view.stop_loading()
            
    def feeds_fetching_started(self, operation_id):
        """
        Actions when feeds will be fetched
        """
        try:
            account = Operation.get_by_id(operation_id).params['object']
        except:
            pass
        else:
            if account == self.account:
                for view in self.views:
                    try:
                        view.feeds_fetching_started()
                    except:
                        pass
            
    def feeds_fetched(self, operation_id):
        """
        Actions when feeds are just fetched
        """
        try:
            account = Operation.get_by_id(operation_id).params['object']
        except:
            pass
        else:
            if account == self.account:
                for view in self.views:
                    try:
                        view.feeds_fetched()
                    except:
                        pass
        
    def feed_content_fetching_started(self, operation_id):
        """
        Action when some of a feed's content will be fetched
        """
        try:
            feed = Operation.get_by_id(operation_id).params['object']
        except:
            pass
        else:
            if feed.account == self.account:
                for view in self.views:
                    try:
                        view.feed_content_fetching_started(feed)
                    except:
                        pass
        
    def feed_content_fetched(self, operation_id):
        """
        Action when some of a feed's content was just fetched
        """
        try:
            feed = Operation.get_by_id(operation_id).params['object']
        except:
            pass
        else:
            if feed.account == self.account:
                for view in self.views:
                    try:
                        view.feed_content_fetched(feed)
                    except:
                        pass
            
    def display_item(self, item):
        """
        Display an item by displaying the itemview view.
        If the specified iem cannot be selected, return to the previous view
        """
        self.switch_view('itemview')
        if not self.itemview_view.set_current_item(item):
            self.switch_view('itemlist', hide_current=True)
            
    def display_next_item(self):
        """
        Display the next available item
        """
        self.itemlist_view.activate_next_item()
            
    def display_previous_item(self):
        """
        Display the previous available item
        """
        self.itemlist_view.activate_previous_item()

    def item_read(self, item):
        """
        Called when an item was marked as read/unread
        """
        for view in self.views:
            try:
                view.item_read(item)
            except:
                pass

    def item_shared(self, item):
        """
        Called when an item was shared/unshared
        """
        for view in self.views:
            try:
                view.item_shared(item)
            except:
                pass

    def item_starred(self, item):
        """
        Called when an item was starred/unstarred
        """
        for view in self.views:
            try:
                view.item_starred(item)
            except:
                pass

    def feed_read(self, feed):
        """
        Called when an feed was marked as read
        """
        for view in self.views:
            try:
                view.feed_read(feed)
            except:
                pass
