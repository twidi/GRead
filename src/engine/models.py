# -*- coding: utf-8 -*-

"""
This module contains all models used by GRead :
* Account
* Category
* Feed
* Item
All these model are tied to something in libgreader, except account which has
no equivalent in libgreader. This is an abstraction of libgreader, so later we 
could use another lib, without having to change whatever use this models.py file.
"""

import sys, re, itertools, time
from operator import attrgetter
from locale import setlocale, strxfrm, LC_ALL
from utils.libgreader import GoogleReader, ClientAuth, Category as gCategory, Feed as gFeed
from engine import settings
from engine.operations import *

class ModelError(Exception):pass
class AccountHasNoFeedsError(ModelError):pass
class DistError(ModelError):pass

# regexp to remove html tags from items' title
RE_REMOVE_TAGS = re.compile(r'<[^<]*?/?>')
# regexp to find feeds in item
RE_ID_USER_PART = re.compile(r'^user/(:?\-|\d+)/')


setlocale(LC_ALL, "")
def locale_keyfunc(keyfunc):
    """
    Utility to sort by string with locale considerations :
    sorted(array_of_objects, key=locale_keyfunc(attrgetter('name')))
    """
    def locale_wrapper(obj):
      return strxfrm(keyfunc(obj))
    return locale_wrapper


class SavedAuth(ClientAuth):
    """
    A subclass of ClientAuth in libgreader to pass directly the tokens (usefull
    in the case they were storred before)
    """
    def __init__(self, username, password, auth_token, token):
        self.client     = settings.legal['application']['name']
        self.username   = username
        self.password   = password
        self.auth_token = auth_token
        self.token      = token

class Account(object):
    """
    A Google Reader account.
    We store it's login, it's password, and a ClientAuth object from 
    libgreader and a list of categories.
    The id is the login
    """
    _current = None
    
    def __init__(self, id=None, password=None):
        """
        Instantiate a new Account
        """
        if not id:
            id = str(settings.get('google', 'account'))
        self.id               = id
        self.categories       = []
        self.categories_by_id = {}
        self.is_authenticated = False
        
        # An operation manager for this account
        self.operations_manager = OperationsManager(self,  callbacks = {
            'get_feed_content_done':      self.operation_get_feed_content_done, 
            'get_more_feed_content_done': self.operation_get_feed_content_done, 
        })
        # ClientAuth object (from libgreader)
        self.g_auth = None
        # GoogleReader object (from libgreader)
        self.g_object = None
        
        # category for special feeds
        self.special_category = None
        # and one for orphan feeds
        self.orphan_feeds_category = None
        
        # total unread count
        self.unread = 0
    
    @classmethod
    def get_current(cls):
        """
        A class method returning the current account
        """
        return cls._current
        
    def authenticate(self):
        """
        Create an asynchronous operation to authenticate this account
        """
        self.operations_manager.add(OperationAuthenticate(object=self))
        
    def dist_authenticate(self):
        """
        Authenticate the account with Google Reader
        """
        was_authenticated = self.is_authenticated
        self.is_authenticated = False
        try:
            # if this account was previously authenticated, we try to get
            # another token
            if self.g_auth and was_authenticated:
                try:
                    sys.stderr.write("AUTH: update token\n")
                    self.g_auth.token = self.g_auth._getToken()
                    sys.stderr.write("AUTH: token=%s\n" % self.g_auth.token)
                    self.is_authenticated = True
                    settings.set('google', 'token', self.g_auth.token, save_all=True)
                except:
                    pass

            # else, but if we already had tokens by the past, try with them
            elif settings.get('google', 'auth_token') and settings.get('google', 'token'):
                sys.stderr.write("AUTH: load saved auth\n")
                self.g_auth = SavedAuth(settings.get('google', 'account'), \
                                        settings.get('google', 'password'), \
                                        settings.get('google', 'auth_token'), \
                                        settings.get('google', 'token'))
                try:
                    # test if the token is still valid
                    self.g_auth.token = self.g_auth._getToken()
                except:
                    pass
                else:
                    # it's valid so we are authenticated
                    settings.set('google', 'token', self.g_auth.token, save_all=True)
                    self.is_authenticated = True
                    
            # here, we have not a valid token, so we do a full authentication
            if not self.is_authenticated:
                sys.stderr.write("AUTH: full auth\n")
                self.g_auth = ClientAuth(settings.get('google', 'account'), settings.get('google', 'password'))
                self.is_authenticated = True
                settings.set('google', 'verified', True)
                settings.set('google', 'auth_token', self.g_auth.auth_token)
                settings.set('google', 'token', self.g_auth.token, save_all=True)

            # finally if we are authenticated, update, or create, a new 
            # GoogleReadr object
            if self.is_authenticated:
                if self.g_object:
                    self.g_object.auth = self.g_auth
                else:
                    self.create_g_object()

        # an exception was raised during the authentication. 
        # it is either a authentication failure, or a network failure
        # but let the caller manage this
        except:
            self.is_authenticated = False
            raise
            
    def assert_authenticated(self):
        """
        Raise an exception if the account is not authenticated
        """
        if not self.is_authenticated:
            raise NotAuthenticatedError("Account is not authenticated")
                
    def create_g_object(self):
        """
        Will create a GoogleReader instance. Also make special category.
        """
        # create the object from libgreader
        self.g_object = GoogleReader(self.g_auth)
        # create the category for special feeds
        self.g_object.makeSpecialFeeds()
        self.special_category = SpecialCategory(self)
        self.add_category(self.special_category)
        
    def add_category(self, category):
        """
        Add an category to this account
        """
        if not category.id in self.categories_by_id:
            self.categories_by_id[category.id] = category
            self.categories.append(category)
            
    def fetch_feeds(self, fetch_unread_content=False):
        """
        Create an asynchronous operation to fetch feeds for this account
        """
        self.operations_manager.add(OperationGetAccountFeeds(
            object=self, fetch_unread_content=fetch_unread_content))
            
    def dist_fetch_feeds(self):
        """
        Get google reader feeds for this account
        """
        self.assert_authenticated()
        
        # get content from Google Reader
        self.g_object.buildSubscriptionList()
        
        # if no content, there is a problem : raise
        g_feeds = self.g_object.getFeeds()
        if not g_feeds:
            raise AccountHasNoFeedsError
        
        # add each category
        for g_category in self.g_object.getCategories():
            category = Category.get_by_id(g_category.id, account=self)
            if not category:
                category = Category(
                    id         = g_category.id, 
                    account    = self, 
                    g_category = g_category, 
                )
                self.add_category(category)
            else:
                category.g_category = g_category
            
        # add each feed
        total_unread = 0
        for g_feed in g_feeds:
            total_unread += g_feed.unread
            feed = Feed.get_by_id(g_feed.id, account=self)
            if not feed:
                feed = Feed(
                    id      = g_feed.id, 
                    account = self, 
                    g_feed  = g_feed, 
                )
            old_unread = feed.unread
            feed.unread = g_feed.unread
            feed.update_missing_unread()
            # now no unread and then we have ones : mark all items as read !
            if old_unread and not feed.unread:
                for item in feed.items:
                    item.unread = True
            # update feed's categories
            for g_category in g_feed.getCategories():
                category = Category.get_by_id(g_category.id, account=self)
                category.add_feed(feed)
                
        # we have orphan feeds ?
        if self.g_object.orphanFeeds:
            if not self.orphan_feeds_category:
                self.orphan_feeds_category = OrphanFeedsCategory(self)
                self.add_category(self.orphan_feeds_category)
            for g_feed in self.g_object.orphanFeeds:
                feed = Feed.get_by_id(g_feed.id, account=self)
                self.orphan_feeds_category.add_feed(feed)
                
        # update unread counts
        self.special_category.special_feeds[GoogleReader.READING_LIST].unread = total_unread
        for feed in self.special_category.feeds:
            if feed.special_type not in (GoogleReader.READING_LIST,  GoogleReader.READ_LIST):
                feed.unread = feed.g_feed.unread
        for category in self.categories:
            category.update_unread()
        self.update_unread()
            
    def fetch_unread_content(self):
        """
        Fetch the unread content for all categories
        """
        # first for normal categories
        for category in self.get_categories(unread_only=True)[1:]:
            category.fetch_content(unread_only=True)
        # then for the special one
        self.special_category.fetch_content(unread_only=True)

    def update_unread(self):
        """
        Update the unread count : number of unread items in all feeds
        """
        self.unread = self.special_category.unread
        return self.unread
        
    def get_categories(self, unread_only=False, order_by=None, reverse_order=None):
        """
        Get the list of all categories, filtering only unread if asked, and
        ordering them as asked.
        order_by can be "title" or "unread" (default None, say as in GoogleReder)
        By default reverse_order is False for "title" and True for "unread"
        """
        result = self.categories[:1] # special category always first

        to_sort = []
        if unread_only:
            to_sort = [category for category in self.categories[1:] if category.unread]
        else:
            to_sort= self.categories[1:]
        
        if order_by == 'title':
            if reverse_order is None:
                reverse_order = False
            result += sorted(to_sort, key=locale_keyfunc(attrgetter('title')),\
                reverse=reverse_order)
        elif order_by == 'unread':
            if reverse_order is None:
                reverse_order = True
            result += sorted(to_sort, key=attrgetter('unread'),\
                reverse=reverse_order)
        else:
            result += to_sort
    
        return result
        
    def category_unread_count_changed(self, category):
        """
        When the unread count of a category has changed, this method is called
        to update the total unread count
        """
        if category != self.special_category:
            self.special_category.update_unread()
        self.update_unread()
    
    @property
    def normal_feeds(self):
        """
        Return feeds excluding special ones
        """
        return [feed for feed in Feed.get_for_account(self) if feed.__class__ == Feed]        
        
    def operation_get_feed_content_done(self, operation):
        """
        Called by the operations manager when a "get_feed_content" or
        "get_more_feed_content" operation is done. If the "max_fetch" parameter
        for this operation is not None, then we have to fetch more content for
        this feed.
        """
        if operation.params.get('max_fetch', None) is not None:
            operation.params['object'].fetch_content_next_part(
                unread_only = operation.params.get('unread_only', False), 
                max_fetch   = operation.params['max_fetch'], 
            )

class _BaseModelForAccount(object):
    """
    A base model class for all models.
    Manage retrieving of objects by id.
    """
    # "_objects_by_id = {}" must be defined in subclasses
    
    def __init__(self, id, account):
        """
        Save the id for this object and add in the _objects_by_id dict
        """
        self.id = id
        self.account = account
        self.__class__.set_by_id(self, account)
    
    @classmethod
    def get_by_id(cls, id, account):
        """
        Return an object of this class identified by it's id
        """
        try:
            return cls._objects_by_id[account.id][id]
        except:
            return None
            
    @classmethod
    def get_for_account(cls, account):
        """
        Get all a list of all objects of this type for the given account
        """
        return cls._objects_by_id.get(account.id, {}).values()

    @classmethod
    def set_by_id(cls, object, account):
        """
        Set an object of this class by it's id
        """
        cls._objects_by_id.setdefault(account.id, {})[object.id] = object

class Category(_BaseModelForAccount):
    """
    A category is a list of feeds. It can be a label in Google Reader or
    another fake category.
    Store the category's id, the original category from libgreader, a 
    list of feeds and the accout it belongs to
    """
    _objects_by_id = {}
    
    def __init__(self, id, account, g_category=None):
        """
        Instantiate a new Category
        """
        super(Category, self).__init__(id, account)
        
        # also save by strict_id
        self.strict_id = RE_ID_USER_PART.sub("", id)
        self.__class__._objects_by_id[account.id][self.strict_id] = self
        
        self.g_category  = g_category
        self.feeds       = []
        self.feeds_by_id = {}
        if g_category:
            self.title = g_category.label

        # default not sorted
        self.sorted = False
        
        # count unread items in this category
        self.unread = 0
        
        # add a special feed with all items for standard category
        self.category_feed = None
        if self.__class__ == Category and self.g_category:
            self.category_feed = CategoryFeed(self)
        
    def add_feed(self, feed, propagate=True):
        """
        Add an feed in this category.
        If propagate is True, add category to the feed too.
        """
        if not feed.id in self.feeds_by_id:
            self.sorted = False
            self.feeds_by_id[feed.id] = feed
            self.feeds.append(feed)
            if propagate:
                feed.add_to_category(self, propagate=False)
                
    def update_unread(self):
        """
        Update the unread count : number of unread items in all it's feeds
        """
        self.unread = sum([feed.unread for feed in self.feeds if feed.__class__ == Feed])
        if self.category_feed:
            self.category_feed.update_unread()
        return self.unread
            
    def count_feeds(self, unread_only=False):
        """
        Count the total number of feeds in this category. Count only unread ones
        if asked
        """
        if unread_only:
            result = sum([1 for feed in self.feeds if feed.unread])
        else:
            result = len(self.feeds)
        if self.category_feed:
            result -= 1
        return result
        
    def get_feeds(self, unread_only=False, order_by=None, reverse_order=None, exclude=None):
        """
        Get the list of all feeds for this category, filtering only unread if 
        asked, and ordering them as asked.
        order_by can be "title", "date" or "unread" (default ""title"")
        By default reverse_order is False for "title" and True for "date" 
        and "unread"
        Only work for "date" if all feeds were specifically fetched
        TODO: sort by order in Google Reader
        """
        
        # sort the list if needed
        if not self.sorted:
            all_feeds = []
            if self.category_feed:
                all_feeds = [self.category_feed, ]
                feeds = self.feeds[1:]
            else:
                feeds = self.feeds
            self.feeds = all_feeds + sorted(feeds, \
                key=locale_keyfunc(attrgetter('title')), reverse=False)
            self.sorted = True
                
        # temporaly remove the category_feed to keep it on first position (but
        # only if we have more than one feed to return
        result = []
        if self.category_feed:
            if len(self.feeds) > 2:
                result = [self.category_feed, ]
            to_sort = self.feeds[1:]
        else:
            to_sort = self.feeds

        # only keep unread items if wanted
        if unread_only:
            to_sort = [feed for feed in to_sort if feed.unread]
            
        if order_by == 'title' or order_by not in ('title', 'date', 'unread'):
            # if sort by title, just use the current list
            if reverse_order is None:
                reverse_order = False
            if reverse_order:
                result += reversed(to_sort)
            else:
                result += to_sort
        elif order_by == 'date':
            # if sort by date, reverse True by default
            if reverse_order is None:
                reverse_order = True
            result += sorted(to_sort, key=attrgetter('date'),\
                reverse=reverse_order)
        elif order_by == 'unread':
            # if sort by unread, reverse True by default
            if reverse_order is None:
                reverse_order = True
            result += sorted(to_sort, key=attrgetter('unread'),\
                reverse=reverse_order)

        # remove feeds to exclude
        if exclude:
            for feed in exclude:
                result.remove(feed)
                
        return result
        
    def feed_unread_count_changed(self, feed):
        """
        When the unread count of a feed has changed, this method is called for
        all the feed's category to update their unread count
        """
        self.update_unread()
        self.account.category_unread_count_changed(self)
        
    def fetch_content(self, unread_only=False, max_fetch=None):
        """
        Create an asynchronous operation to fetch content for this category.
        If max_fetch == -1, fetch while items are present in the category
        else stop when all or at least max_fetch is retrieved.
        """
        if max_fetch == None:
            max_fetch = int(settings.get('feeds', 'unread_number'))
        if self.category_feed:
            self.category_feed.fetch_content(unread_only=unread_only, max_fetch=max_fetch)        
                
class SpecialCategory(Category):
    """
    A special category which hold for an account its special feeds, like 
    "all", "shared", "starred", "friends"...
    """

    def __init__(self, account):
        """
        Create a fake category in libgreader and then here, and add 
        special feeds to it
        """
        id = 'specials'
        self.base_unread = 0
        
        # create the fake category
        g_special_category = gCategory(account.g_object, "Specials", id)
        super(SpecialCategory, self).__init__(
            id         = g_special_category.id, 
            account    = account, 
            g_category = g_special_category, 
        )
        
        self.special_feeds = {}
        self.special_feeds_by_strict_id = {}
        
        # create and add special feeds
        for special_type in settings.special_feeds:
            feed = SpecialFeed(account, special_type)
            self.add_feed(feed)
            self.special_feeds[special_type] = feed
            
    def add_feed(self, feed, *args, **kwargs):
        """
        When adding a feed to the special category, we may need to acces it by
        it's strict id (without the "user/-/" part)
        """
        super(SpecialCategory, self).add_feed(feed, *args, **kwargs)
        self.special_feeds_by_strict_id[feed.strict_id] = feed

    def update_unread(self):
        """
        Update the unread count : all unread normal feeds + the unread in friends list
        """
        self.unread = sum([feed.unread for feed in self.account.normal_feeds]) +\
            self.special_feeds[GoogleReader.FRIENDS_LIST].unread
        return self.unread
        
    def fetch_content(self, unread_only=False, max_fetch=None):
        """
        Create an asynchronous operation to fetch content for this category.
        If max_fetch == -1, fetch while items are present in the category
        else stop when all or at least max_fetch is retrieved.
        """
        if max_fetch == None:
            max_fetch = int(settings.get('feeds', 'unread_number'))
        for feed in self.get_feeds(unread_only==False, exclude=[
                self.special_feeds[GoogleReader.READING_LIST], 
                self.special_feeds[GoogleReader.READ_LIST], 
            ]):
            feed.fetch_content(unread_only=False, max_fetch=max_fetch) 
                    
class OrphanFeedsCategory(Category):
    """
    A special category which hold for an account its orphan feeds (those
    whitout real category
    """
    
    def __init__(self, account):
        """
        Create a fake category in libgreader
        """
        # create the fake category
        g_special_category = gCategory(account.g_object, "Orphan feeds", 'orphans')
        super(OrphanFeedsCategory, self).__init__(
            id         = g_special_category.id, 
            account    = account, 
            g_category = g_special_category, 
        )
        
    def fetch_content(self, unread_only=False, max_fetch=None):
        """
        Create an asynchronous operation to fetch content for this category.
        If max_fetch == -1, fetch while items are present in the category
        else stop when all or at least max_fetch is retrieved.
        """
        if max_fetch == None:
            max_fetch = int(settings.get('feeds', 'unread_number'))
        for feed in self.get_feeds(unread_only=unread_only):
            feed.fetch_content(unread_only=unread_only, max_fetch=max_fetch) 

class Feed(_BaseModelForAccount):
    """
    A feed is an list of items. It can be a feed in Google Reader or another
    fake feed.
    Store the feed's id, the original feed from libgreader, categories to 
    which it belongs and a list of items
    """
    _objects_by_id = {}
    
    def __init__(self, id, account, g_feed=None):
        """
        Instantiate a new Feed
        """
        super(Feed, self).__init__(id, account)
        self.g_feed      = g_feed
        self.categories  = []
        self.items       = []
        self.items_by_id = {}
        if self.g_feed:
            self.title = self.g_feed.title

        # the minimum date fetched during the last fetch
        self.last_min_date_fetched = time.time()

        # default not sorted
        self.sorted = False

        # load status
        self.is_loading = False
        
        # count unread items in this feed
        self.unread = 0
        if self.g_feed:
            self.unread = self.g_feed.unread
            
        # if some unread items are not fetched
        self.missing_unread = True
        
        # save continuation_id for the two modes (True for unread_only)
        self.continuation_id = {True: None, False: None}
        # save if a content was fetched in the two modes (True for unread_only)
        self.content_fetched = {True: False, False: False}
        
    def add_item(self, item, propagate=True):
        """
        Add an item in this feed (and in the "category_feed" of all
        it's categories)
        If propagate is True, add the feed to the item too.
        """
        if not item.id in self.items_by_id:
            self.sorted = False
            self.items_by_id[item.id] = item
            self.items.append(item)
            if propagate:
                item.add_to_feed(self, propagate=False)
            # add it in all "category_feed"
            for category in self.categories:
                if category.category_feed\
                    and category.category_feed != self:
                    category.category_feed.add_item(item)
        
    def remove_item(self, item, propagate=True):
        """
        Remove an item from this feed (and from the "category_feed" of all
        it's categories)
        If propagate is True, remove the feed from the item too.
        """
        if item.id in self.items_by_id:
            del self.items_by_id[item.id]
            self.items.remove(item)
            if propagate:
                item.remove_from_feed(self, propagate=False)
            # remove it from all "category_feed"
            for category in self.categories:
                if category.category_feed\
                    and category.category_feed != self:
                    category.category_feed.remove_item(item)
        
    def add_to_category(self, category, propagate=True):
        """
        Add this item into a category
        If propagate is True, add category to the item too.
        """
        if category not in self.categories:
            self.categories.append(category)
            if propagate:
                category.add_feed(self, propagate=False)
                
    def update_parents(self):
        """
        Force all parents to update their unread counter
        """
        for category in self.categories:
            category.feed_unread_count_changed(self)
             
    def mark_as_read(self, local_only=False):
        """
        Mark all items in the feed as read locally and add an operation to do 
        the mark the feed as read on Google Reader
        If local_only is True, don't make feed unread on Google Reader (usefull
        when marking as read a CategoryFeed as we don't have to mark all feeds
        as read on Google Reader, but just locally)
        """
        if not local_only:
            self.account.operations_manager.add(OperationMarkFeedRead(object=self))
        for item in self.get_items(unread_only=True):
            item.mark_as_read(mark_dist=False)
        self.unread = 0        
        self.update_parents()
          
    def dist_mark_as_read(self):
        """
        Mark the feed as read. This operation cannot be undone, and none of
        it's items may be marked as unread
        """
        self.g_feed.markAllRead()
        
    def loaded_items_done(self, g_items=None, unread_only=False):
        """
        When g_items are created, we can create/update items here
        """
        unread_only = not not unread_only
        self.continuation_id[unread_only] = self.g_feed.continuation
        self.content_fetched[unread_only] = True

        if not g_items: g_items = []
        can_have_more_unread = True

        # action for each item if g_feed
        for g_item in g_items:
            # exits ?
            item = Item.get_by_id(g_item.id, account=self.account)
            if not item:
                # if not, create it
                item = Item(
                    id      = g_item.id, 
                    account = self.account, 
                    g_item  = g_item, 
                )
            else:
                # if exists, update it's g_item
                item.dist_update(g_item)
                
            if item.date < self.last_min_date_fetched:
                self.last_min_date_fetched = item.date
                
            # maybe we have a feed for this item not already saved
            if g_item.feed:
                feed = Feed.get_by_id(g_item.feed.id, account=self.account)
                if not feed:
                    feed = Feed(
                        id      = g_item.feed.id, 
                        account = self.account, 
                        g_feed  = g_item.feed, 
                    )
                feed.add_item(item)
            
            # if item cannot be marked as read, no more items will be unread
            if can_have_more_unread and not item.can_unread:
                can_have_more_unread = False
                
            # add the item to this feed
            self.add_item(item)
                
            # change in categories and statuses
            item.update_parents(ignore_categories=self.__class__ != Feed)

        # update unread counts
        self.missing_unread = can_have_more_unread            
        self.update_parents()
        
    def fetch_content(self, unread_only=False, max_fetch=None):
        """
        Create an asynchronous operation to fetch content for this feed
        If max_fetch is not None (or 0), We want to try to continue fetching 
        after this one is done (Google Reader give us only a few items (20) for
        each fetch). If max_fetch is -1, we never stop until Google Reader says
        it has no more content.
        WARNING : having unread_only=False and max_fetch=-1 will retrieve ALL 
        the feed's content (may be thousands of items !)
        """
        self.is_loading = True
        # flag all items as not verified
        self.last_min_date_fetched = time.time()
        for item in self.items:
            for status in ('unread', 'shared', 'starred'):
                item.status_verified[status] = False
        # create the operation
        self.account.operations_manager.add(OperationGetFeedContent(
            object      = self,
            unread_only = unread_only,
            max_fetch   = max_fetch
        ))
        
    def fetch_content_next_part(self, unread_only=False, max_fetch=None):
        """
        If for the previous fetch a max_fetch parameter was set, then we need
        to fetch more content based on the max_fetch parameter. See 
        fetch_content for more informations.
        Return True/False if all unread items were fetched after this part if it is 
        the last one, or None if another part is needed
        """
        previous_max_fetch = max_fetch
        if max_fetch is None or not self.can_fetch_more(unread_only):
            max_fetch = 0
        elif max_fetch != -1:
            max_fetch -= self.previously_loaded_items()
            if max_fetch < 1:
                max_fetch = 0
        if max_fetch != 0:
            self.fetch_more_content(unread_only = unread_only, max_fetch = max_fetch)
            return None
        else:
            # here, the full fetch is done.
            
            # update some unread status for the feed
            all_unread_fetched = (previous_max_fetch == -1 or \
                not self.can_fetch_more(unread_only))
            if all_unread_fetched:
                self.missing_unread = False
            else:
                self.update_missing_unread()
            # we flag item not fetched as needed and set them to verified
            for item in self.items:
                if (all_unread_fetched or item.date >= self.last_min_date_fetched) \
                    and not item.status_verified['unread']:
                        if item.unread:
                            item.mark_as_read(mark_dist=False)
                        else:
                            item.status_verified['unread'] = True
            # maybe the total unread number is not good anymore
            total_unread_count   = self.count_items(unread_only=True)
            if all_unread_fetched:
                fetched_unread_count = total_unread_count
            else:
                fetched_unread_count = self.count_items(unread_only=True, min_date=self.last_min_date_fetched)
            if not self.unread:
                self.unread = fetched_unread_count
            elif all_unread_fetched and self.unread != total_unread_count:
                self.unread = total_unread_count
            self.update_parents()
            return all_unread_fetched
                            
        
    def dist_fetch_content(self, unread_only=False):
        """
        Fetch the content of this feed with Google Reader
        """
        self.is_loading = True
        self.g_feed.loadItems(excludeRead=unread_only)

        if self.g_feed.lastLoadOk:
            # action for each item if g_feed
            self.loaded_items_done(self.g_feed.getItems(), unread_only=unread_only)

        self.is_loading = False
        
    def fetch_more_content(self, unread_only=False, max_fetch=None):
        """
        Create an asynchronous operation to fetch more content for this feed.
        For max_fetch parameters, see the "fetch_content" method.
        """
        unread_only = not not unread_only
        if not self.content_fetched[unread_only]:
            return self.fetch_content(unread_only=unread_only, max_fetch=max_fetch)
        self.is_loading = True
        self.account.operations_manager.add(OperationGetMoreFeedContent(
            object          = self,
            unread_only     = unread_only,
            max_fetch       = max_fetch, 
            contiunation_id = self.continuation_id[unread_only],
        ))
        
    def dist_fetch_more_content(self, unread_only=False, continuation_id=None):
        """
        Fetch more content for this feed with Google Reader
        """
        self.is_loading = True
        old_nb_items = self.g_feed.countItems()
        
        self.g_feed.loadMoreItems(excludeRead=unread_only, continuation=continuation_id)

        if self.g_feed.lastLoadOk:
            # action for each item if g_feed
            self.loaded_items_done(self.g_feed.getItems()[old_nb_items:], unread_only=unread_only)
        self.is_loading = False            
        
    def update_missing_unread(self):
        """
        Calculate if all unread items are retrieved
        """
        if not self.unread:
            self.missing_unread = False
        else:
            self.missing_unread = self.unread != sum([1 for i in self.items if i.unread])
                                
    def item_read_status_changed(self, item, now_unread):
        """
        Called when the read/unread status of an item was changed.
        now_unread is the new status of the item
        """
        delta = -1
        if now_unread:
            delta = 1
        self.unread += delta
        if self.unread < 0: 
            self.unread = 0
        self.update_parents()
            
    def count_items(self, unread_only=False, min_date=None):
        """
        Count the total number of items in this feed. Count only unread ones
        if asked, and limit to items older than min_date if asked
        """
        if unread_only:
            if not min_date:
                return sum([1 for item in self.items if item.unread])
            else:
                return sum([1 for item in self.items if item.unread and item.date >= min_date])
        else:
            if not min_date:
                return len(self.items)
            else:
                return sum([1 for item in self.items if item.date >= min_date])
        
    def get_items(self, unread_only=False, order_by=None, reverse_order=None):
        """
        Get the list of all items for this feed, filtering only unread if 
        asked, and ordering them as asked.
        order_by can be "title" or "date" (default "date"" with reverse_order 
        True)
        By default reverse_order is False for "title" and True for "date"
        """

        # sort the list if needed
        if not self.sorted:
            self.items.sort(key=attrgetter('date'), reverse=True)
            self.sorted = True

        # get only unread items if wanted
        if unread_only:
            to_sort = [item for item in self.items if item.unread]
        else:
            to_sort = self.items
            
        if order_by == 'title':
            # if sort by title, create a new sorted list
            if reverse_order is None:
                reverse_order = False
            return sorted(to_sort, key=locale_keyfunc(attrgetter('title')),\
                reverse=reverse_order)
        elif order_by == 'date' or order_by not in ('title', 'date'):
            # if sort by date, use directly the items list
            if reverse_order is None:
                reverse_order = True
            if reverse_order:
                return to_sort
            else:
                return reversed(to_sort)
            
    def can_fetch_more(self, unread_only):
        """
        Return True if more items can be fetched for this feed
        """
        if not self.content_fetched[unread_only]:
            return True
        return not not self.continuation_id[unread_only]
        
    def previously_loaded_items(self):
        """
        Returns the number of items loaded during the last fetch (or fetch-more)
        """
        return self.g_feed.lastLoadLength
        
    @property
    def date(self):
        """
        Return the date Google Reader updated this feed. It's a property
        """
        try:
            result = self.g_feed.lastUpdated
            if result:
                return result
            return self.items[0].date
        except:
            return time.time()
        
class SpecialFeed(Feed):
    """
    A special feed like "all", "shared", "friends"...
    """
    def __init__(self, account, special_type):
        """
        Create the libgreader special feed and create one here
        """
        g_feed       = account.g_object.getSpecialFeed(special_type)
        g_feed.title = settings.special_feeds[special_type]['name']
        super(SpecialFeed, self).__init__(
            id      = g_feed.id,
            account = account, 
            g_feed  = g_feed, 
        )
        self.special_type = special_type
        self.strict_id = RE_ID_USER_PART.sub("", self.id)
        
class CategoryFeed(Feed):
    """
    A special feed which contains items for all feeds in the category
    """
    def __init__(self, category):
        """
        Create a fake gFeed object, and then a Feed object
        """
        # create a fake gFeed object
        g_feed= gFeed(
            category.account.g_object,
            title      = 'All for "%s"' % category.title,
            id         = category.id,
            unread     = category.unread, 
            categories = [], 
        )
        g_feed.fetchUrl = category.g_category.fetchUrl
        g_feed.category  = category.g_category

        # now create the Feed object
        super(CategoryFeed, self).__init__(
            id      = category.id, 
            account = category.account, 
            g_feed  = g_feed
        )

        # and automatically add it to it's category
        self.add_to_category(category)
        
    def update_unread(self):
        """
        The unread count of this feed is its category unread count
        """
        self.unread = self.categories[0].unread
        self.update_missing_unread()
        return self.unread
             
    def mark_as_read(self, *args, **kwargs):
        """
        Call the inherited method and then update unread count for all feeds 
        in the category of this special feed
        Mark all items in the feed as read locally and add an operation to do 
        the mark the feed as read on Google Reader
        """
        super(CategoryFeed, self).mark_as_read(*args, **kwargs)
        for feed in self.categories[0].get_feeds(unread_only=True, exclude=[self, ]):
            feed.mark_as_read(local_only=True)

    def fetch_content_next_part(self, unread_only=False, max_fetch=None):
        """
        """
        all_unread_fetched = super(CategoryFeed, self).fetch_content_next_part(
            unread_only, max_fetch)
        if all_unread_fetched != True:
            return
        for feed in self.categories[0].get_feeds():
            feed.content_fetched[unread_only] = True
        

class Item(_BaseModelForAccount):
    """
    An item is an entry in a feed. It can be a item in Google Reader or 
    another fake item.
    Store the item's id, the original item from libgreader, a list of feeds it
    belongs
    """
    _objects_by_id = {}
    
    def __init__(self, id, account, g_item=None):
        """
        Instantiate a new item
        """
        super(Item, self).__init__(id, account)
        self.feeds  = []
        
        # default values
        self.unread     = False
        self.shared     = False
        self.starred    = False
        self.can_unread = False
            
        # set to True when just checked from Google Reader
        self.status_verified = {
            'unread':  False, 
            'shared':  False, 
            'starred': False
        }

        # if we have a g_item, update this item
        self.dist_update(g_item)

    def dist_update(self, g_item=None):
        """
        Update a local item with an item from Google Reader
        """
        if not g_item:
            return
        self.g_item     = g_item
        self.unread     = g_item.isUnread()
        self.shared     = g_item.isShared()
        self.starred    = g_item.isStarred()
        self.can_unread = g_item.canUnread
        self.title      = RE_REMOVE_TAGS.sub('', g_item.title)
        self.url        = g_item.url
        self.content    = g_item.content
        try:
            self.date   = float(g_item.data['crawlTimeMsec']) / 1000
        except:
            self.date   = time.time()
        for status in self.status_verified:
            self.status_verified[status] = True
        
    def add_to_feed(self, feed, propagate=True):
        """
        Add this item into a feed
        If propagate is True, add feed to the item too.
        """
        if feed not in self.feeds:
            self.feeds.append(feed)
            if propagate:
                feed.add_item(self, propagate=False)
        
    def remove_from_feed(self, feed, propagate=True):
        """
        Remove this item from a feed
        If propagate is True, remove feed from the item too.
        """
        if feed in self.feeds:
            self.feeds.remove(feed)
            if propagate:
                feed.remove_item(self, propagate=False)
                
    @property
    def normal_feeds(self):
        """
        Return the normal feeds in which this item is
        """
        normal_feeds = list(set(self.feeds).difference(
                set(self.account.special_category.special_feeds.values())
            )
        )
        return [feed for feed in normal_feeds if not isinstance(feed, CategoryFeed)]
        
    @property
    def special_feeds(self):
        """
        Return the special feeds in which this item is present
        """
        return list(set(self.feeds).intersection(
                set(self.account.special_category.special_feeds.values())
            )
        )
                
    def propagate_unread_status(self, now_unread):
        """
        Propagate the unread_status to feeds, so they can update
        there unread count
        """
        for feeds in self.feeds:
            feeds.item_read_status_changed(self, now_unread)

    def update_parents(self, ignore_categories=False):
        """
        When an item was fetched, we have to update the categories and
        special feeds in which it appears
        """
        reading_list = self.account.special_category.special_feeds[GoogleReader.READING_LIST].strict_id
        notes_list   = self.account.special_category.special_feeds[GoogleReader.NOTES_LIST].strict_id

        # each actual categories and "status" for this item
        old_cats = set(RE_ID_USER_PART.sub("", c.id) \
            for c in itertools.chain(*[f.categories for f in self.feeds]))
        # remove the special category
        try: old_cats.remove(self.account.special_category.id)
        except: pass
        old_cats.update([RE_ID_USER_PART.sub("", f.id) for f in self.feeds \
            if isinstance(f, SpecialFeed)])
        # remove the reading list and notes list
        try: old_cats.remove(reading_list)
        except: pass
        try: old_cats.remove(notes_list)
        except: pass
        
        # each categories ans "status" for this item in Google Reader
        new_cats  = set([RE_ID_USER_PART.sub("", id) \
            for id in self.g_item.data.get('categories', []) \
            if RE_ID_USER_PART.match(id)])
            
        # check in which cat we have to add/remove this item
        cats_to_add = new_cats.difference(old_cats)
        cats_to_rem = old_cats.difference(new_cats)
        
        # start to add cats
        for cat_id in cats_to_add:
            if cat_id.startswith('label/') and not ignore_categories:
                # it's a real cat, if it exists, add this item
                # to it's category_feed (the "all" one)
                category = Category.get_by_id(cat_id, self.account)
                if category and category.category_feed:
                    category.category_feed.add_item(self)
            elif cat_id.startswith('state/com.google/'):
                # else, it's a "status", so we can add the item
                # in a feed in the special category
                special_feed = self.account.special_category\
                    .special_feeds_by_strict_id.get(cat_id, None)
                if special_feed:
                    special_feed.add_item(self)
                    
        # and now remove old cats
        for cat_id in cats_to_rem:
            if cat_id.startswith('label/') and not ignore_categories:
                # it's a real cat, if it exists, remove this item
                # from it's category_feed (the "all" one)
                category = Category.get_by_id(cat_id, self.account)
                if category and category.category_feed:
                    category.category_feed.remove_item(self)
            elif cat_id.startswith('state/com.google/'):
                # else, it's a "status", so we can remove the item
                # from a feed in the special category
                special_feed = self.account.special_category\
                    .special_feeds_by_strict_id.get(cat_id, None)
                if special_feed:
                    special_feed.remove_item(self)
        
    def mark_as_read(self, mark_dist=True):
        """
        Mark the item as read locally and add an operation to do the same
        on Google Reader
        """
        self.status_verified['unread'] = True
        if self.unread:
            self.unread = False
            self.g_item.read = True
            self.propagate_unread_status(now_unread=False)
            if mark_dist:
                self.account.operations_manager.add(OperationMarkItemRead(object=self))
            
    def dist_mark_as_read(self):
        """
        Mark the item as read in Google Reader
        """
        if not self.g_item.markRead():
            raise DistError("Item could not be marked as read")
        
    def mark_as_unread(self, mark_dist=True):
        """
        Mark the item as unread locally and add an operation to do the same
        on Google Reader
        """
        self.status_verified['unread'] = True
        if not self.unread:
            self.unread = True
            self.g_item.read = False
            self.propagate_unread_status(now_unread=True)
            if mark_dist:
                self.account.operations_manager.add(OperationMarkItemUnread(object=self))
            
    def dist_mark_as_unread(self):
        """
        Mark the item as unread in Google Reader
        """
        if not self.g_item.markUnread():
            raise DistError("Item could not be marked as unread")
        
    def share(self, mark_dist=True):
        """
        Share this item locally and add an operation to do the same
        on Google Reader
        """
        self.status_verified['shared'] = True
        if not self.shared:
            self.shared = True
            self.g_item.shared = True
            if mark_dist:
                self.account.operations_manager.add(OperationShareItem(object=self))
            
    def dist_share(self):
        """
        Share this item in Google Reader
        """
        if not self.g_item.share():
            raise DistError("Item could not be shared")
        
    def unshare(self, mark_dist=True):
        """
        Unshare this item locally and add an operation to do the same
        on Google Reader
        """
        self.status_verified['shared'] = True
        if self.shared:
            self.shared = False
            self.g_item.shared = False
            if mark_dist:
                self.account.operations_manager.add(OperationUnshareItem(object=self))
            
    def dist_unshare(self):
        """
        Uhare this item in Google Reader
        """
        if not self.g_item.unShare():
            raise DistError("Item could not be unshared")
        
    def star(self, mark_dist=True):
        """
        Star this item locally and add an operation to do the same
        on Google Reader
        """
        self.status_verified['starred'] = True
        if not self.starred:
            self.starred = True
            self.g_item.starred = True
            if mark_dist:
                self.account.operations_manager.add(OperationStarItem(object=self))
            
    def dist_star(self):
        """
        Star this item in Google Reader
        """
        if not self.g_item.star():
            raise DistError("Item could not be starred")
        
    def unstar(self, mark_dist=True):
        """
        Unstar this item locally and add an operation to do the same
        on Google Reader
        """
        self.status_verified['starred'] = True
        if self.starred:
            self.starred = False
            self.g_item.starred = False
            if mark_dist:
                self.account.operations_manager.add(OperationUnstarItem(object=self))
            
    def dist_unstar(self):
        """
        Unstar this item in Google Reader
        """
        if not self.g_item.unStar():
            raise DistError("Item could not be unstarred")
