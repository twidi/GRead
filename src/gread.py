#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
TODO:

- manage read for SpecialFeed: unread count
- zoom content
- update feed list unread count of a feed when it's reloaded
- add google search feeds with links like https://www.google.com/reader/api/0/feed-finder?q=twidi&output=json
- preload feeds after subscribing list (preload the n last items, n updatable in settings)
"""
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from ui import UiController
from operation import Operation, OperationManager
from utils.libgreader import GoogleReader, ClientAuth, Category, Feed, BaseFeed
import sys, re
sys.setdefaultencoding("utf-8")

REMOVE_TAGS = re.compile(r'<[^<]*?/?>')

DEBUG = True

QApplication.setOrganizationName("Twidi.com")
QApplication.setOrganizationDomain("twidi.com")
QApplication.setApplicationName("Gread")

class CategoryFeed(BaseFeed):
    def __init__(self, googleReader, category):
        super(CategoryFeed, self).__init__(
            googleReader,
            title      = 'All for "%s"' % category.label,
            id         = category.id,
            unread     = category.unread, 
            categories = [], 
        )
        
        self.fetchUrl = category.fetchUrl
        self.category = category
        category.category_feed = self
        
    def countUnread(self):
        self.unread = self.category.unread

class GRead(object):
    settings_helpers = {
        'feeds_default': ['feeds', 'labels', ], # list and not tuple for using index method
        'feeds_all_entries': ['hide', 'top', 'bottom', ], 

        'feeds_specials': GoogleReader.SPECIAL_FEEDS,
        
        'items_show_mode': ('all-save', 'updated-save', 'all-nosave', 'updated-nosave'), 

        'booleans': (
            'google.verified',
                     
            'feeds.show_' + GoogleReader.STARRED_LIST, 
            'feeds.show_' + GoogleReader.SHARED_LIST, 
            'feeds.show_' + GoogleReader.READING_LIST, 
            'feeds.show_' + GoogleReader.READ_LIST, 
            'feeds.show_' + GoogleReader.NOTES_LIST, 
            'feeds.show_' + GoogleReader.FRIENDS_LIST, 
            'feeds.show_' + GoogleReader.KEPTUNREAD_LIST, 

            'feeds.show_updated',
            
            'other.auto_rotation', 
        ), 
    }
    special_feeds = {
        GoogleReader.STARRED_LIST:    { 'name': 'Starred',}, 
        GoogleReader.SHARED_LIST:     { 'name': 'Shared',}, 
        GoogleReader.READING_LIST:    { 'name': 'All',}, 
        GoogleReader.READ_LIST:       { 'name': 'Read',}, 
        GoogleReader.NOTES_LIST:      { 'name': 'Notes',}, 
        GoogleReader.FRIENDS_LIST:    { 'name': 'Friends',}, 
        GoogleReader.KEPTUNREAD_LIST: { 'name': 'Kept unread',}, 
    }
    settings = {
        'google': {
            'account': '',
            'password': '',
            'verified': False,
            'auth_token': '', 
            'token': '', 
        },
        'feeds': {
            'default':     'feeds', # feeds or labels
            'show_updated': True, # display all, or only updated feeds
            'all_entries':  'top', # display a "all for this label" entry for each label
            # special lists : 
            'show_' + GoogleReader.STARRED_LIST:   True,
            'show_' + GoogleReader.SHARED_LIST:     False, 
            'show_' + GoogleReader.READING_LIST:    False,
            'show_' + GoogleReader.READ_LIST:       False,
            'show_' + GoogleReader.NOTES_LIST:      False,
            'show_' + GoogleReader.FRIENDS_LIST:    True,
            'show_' + GoogleReader.KEPTUNREAD_LIST: False,
        }, 
        'items': {
            'show_mode': 'updated-save', # all-save, updated-save, all-nosave, updated-nosave
        }, 
        'other': {
            'auto_rotation': False, 
        }
    }
                
    def __init__(self):

        self.authenticated            = False
        self.previously_authenticated = False
        self.subscription_list_built  = False
        self.sync_ok                  = False

        self.ui      = None
        self.greader = None
        self.auth    = None
        
        self.special_category = None

        self.total_unread = 0
        
        self.operation_manager = OperationManager(self, test_auth_url=GoogleReader.USER_INFO_URL)
        QObject.connect(self.operation_manager, SIGNAL("display_message"), self.display_message, Qt.QueuedConnection)
        QObject.connect(self.operation_manager, SIGNAL("sync_done"), self.sync_done, Qt.QueuedConnection)
        QObject.connect(self.operation_manager, SIGNAL("sync_error"), self.sync_error, Qt.QueuedConnection)
        
        self.load_settings()

    def load_settings(self):
        """
        Load settings from file or whatever
        """
        settings = QSettings()
        for group in self.settings:
            settings.beginGroup(group)
            for key in self.settings[group]:
                value = settings.value(key, self.settings[group][key])
                if '%s.%s' % (group, key) in self.settings_helpers['booleans']:
                    self.settings[group][key] = value.toBool()
                else:
                    self.settings[group][key] = value.toString()
            settings.endGroup()

    def save_settings(self, update_ui=True):
        """
        Save settings into file or whatever
        """
        settings = QSettings()
        for group in self.settings:
            settings.beginGroup(group)
            for key in self.settings[group]:
                 settings.setValue(key, self.settings[group][key])
            settings.endGroup()

        if update_ui:
            self.update_special_category()
            if self.ui:
                self.ui.settings_updated()
                
    def auth_settings_ready(self):
        return (self.settings['google']['account'].replace(' ', '') != '' and self.settings['google']['password'].replace(' ', '') != '')
        
    def run(self):
        """
        Launch the application and then exit when closed
        """
        app = QApplication(sys.argv)
        self.ui = UiController(gread = self)
        self.ui.show(app_just_launched=True)
        result = app.exec_()
        if DEBUG and Operation.done: 
            print "Operations done :"
            for op in Operation.done:
                print "\t%s" % op
                for error in op.errors:
                    print "\t\t%s" % error
        sys.exit(result)
        
    def display_message(self, message, level="information"):
        self.ui.display_message(message, level)

    def sync_done(self):
        if self.sync_ok:
            self.update_special_category()
            self.ui.sync_done(True)
        self.ui.stop_loading()
        
    def sync_error(self):
        self.ui.sync_done(False)
        self.ui.stop_loading()

    def sync(self):
        """
        Sync local data with google reader
        Return True if feeds are retrieved
        """
        self.sync_ok = False
        
        if not self.authenticated:
            self.operation_manager.set_not_authenticated(False)
        if not self.authenticated:
            self.operation_manager.display_message("Error getting the Auth token, have you entered a correct username and password?")
            return False

        self.greader.buildSubscriptionList()
        self.greader.makeSpecialFeeds()

        feeds = self.get_feeds()
        if feeds:
            subscription_list_built = True
            self.total_unread = sum([feed.unread for feed in feeds])
        else:
            self.operation_manager.display_message("No feeds retrieved", level="critical")
            return False
        
        self.sync_ok = True
        return True
        
    def get_home_content(self, updated_only=False, current_category=None):
        result = []
        
        categories = list(self.get_categories(updated_only))
        if self.special_category.getFeeds():
           categories.insert(0, self.special_category)

        for category in categories:
            result.append(category)
            if self.settings['feeds']['default'] == 'feeds' \
            or (current_category is not None and category.id == current_category.id):

                feeds = []
                for feed in category.getFeeds():
                    if category.id == 'specials' or not updated_only or feed.unread:
                        feeds.append(feed)

                all_feed = None
                if len(feeds) > 1 and self.settings['feeds']['all_entries'] != 'hide' and category.id != 'specials':
                    all_feed = CategoryFeed(self.greader, category)
                    if self.settings['feeds']['all_entries'] == 'top':
                        feeds.insert(0, all_feed)
                    else:
                        feeds.append(all_feed)

                result += feeds

        return result
        
    def get_categories(self, updated_only=False):
        """
        Get all categories retrieved from google reader (only these with unread items if updated_only is True)
        """
        categories = self.greader.getCategories()
        if updated_only:
            return [category for category in categories if category.unread]
        else:
            return categories
        
        
    def get_feeds(self, updated_only=False):
        """
        Get all feeds retrieved from google reader (only these with unread items if updated_only is True)
        """
        feeds = self.greader.getFeeds()
        if updated_only:
            return [feed for feed in feeds if feed.unread]
        else:
            return feeds
            
    def count_unread(self):
        self.total_unread = sum([feed.unread for feed in self.greader.getFeeds()])
        
    def authenticate(self):
        """
        Authenticate user with google reader
        """
        was_authenticated = self.authenticated
        self.authenticated = False
        try:
            if self.auth and was_authenticated:
                try:
                    print "AUTH: update token"
                    self.auth.token = self.auth._getToken()
                    print "AUTH: token=%s" % self.auth.token
                    self.authenticated = True
                    self.settings['google']['token'] = self.auth.token
                    self.save_settings(update_ui=False)
                except Exception, e:
                    pass

            elif self.settings['google']['auth_token'] and self.settings['google']['token']:
                print "AUTH: load saved auth"
                self.auth = SavedAuth(self.settings['google']['account'], self.settings['google']['password'], \
                                      self.settings['google']['auth_token'], self.settings['google']['token'])
                try:
                    self.auth.token = self.auth._getToken()
                except:
                    pass
                else:
                    self.settings['google']['token'] = self.auth.token
                    self.save_settings(update_ui=False)
                    self.authenticated = True

            if not self.authenticated:
                print "AUTH: full auth"
                self.auth = ClientAuth(self.settings['google']['account'], self.settings['google']['password'])
                self.authenticated = True
                self.settings['google']['verified'] = True
                self.settings['google']['auth_token'] = self.auth.auth_token
                self.settings['google']['token'] = self.auth.token
                self.save_settings(update_ui=False)

            if self.authenticated:
                self.previously_authenticated = True
                if self.greader:
                    self.greader.auth = self.auth
                else:
                    self.greader = GoogleReader(self.auth)

        except:
            self.authenticated = False
            raise
        
    def update_special_category(self):
        if not self.authenticated:
            return
        if not self.special_category:
            self.special_category = Category(self.greader, 'Specials', 'specials')
            
        for feed in self.special_category.feeds:
            feed.categories = []
        self.special_category.feeds = []
        for special_type in self.settings_helpers['feeds_specials']:
            if self.settings['feeds']['show_%s' % special_type]:
                info = self.special_feeds[special_type]
                feed = self.greader.getSpecialFeed(special_type)
                feed.title = self.special_feeds[special_type]['name']
                feed._addCategory(self.special_category)
            
    def get_feed_content(self, feed, updated_only=False):
        feed.loadItems(excludeRead=updated_only)
        if feed.lastLoadOk:
            for item in feed.getItems():
                item.title = REMOVE_TAGS.sub('', item.title)
        return feed.lastLoadOk
        
    def get_more_feed_content(self, feed, updated_only=False):
        feed.loadMoreItems(excludeRead=updated_only)
        if feed.lastLoadOk:
            for item in feed.getItems():
                item.title = REMOVE_TAGS.sub('', item.title)
        return feed.lastLoadOk
                    
    def feed_mark_read(self, feed):
        return feed.markAllRead()
            
    def item_mark_read(self, item):
        return item.markRead()

    def item_mark_unread(self, item):
        return item.markUnread()
        
    def item_share(self, item):
        return item.share()
        
    def item_unshare(self, item):
        return item.unShare()

    def item_star(self, item):
        return item.star()
        
    def item_unstar(self, item):
        return item.unStar()

class SavedAuth(ClientAuth):
    def __init__(self, username, password, auth_token, token):
        self.client = "libgreader"
        self.username = username
        self.password = password
        self.auth_token = auth_token
        self.token = token


if __name__ == "__main__":
    gread = GRead()
    gread.run()
