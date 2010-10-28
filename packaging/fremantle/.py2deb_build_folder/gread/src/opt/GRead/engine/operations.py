# -*- coding: utf-8 -*-

"""
A module for managing operations againt Google Reader.
Operations are asynchronous, threaded, and splited in many queues.
"""

__all__ = [
    'NotAuthenticatedError', 
    'OperationsManager', 
    'OperationGetAccountFeeds', 'OperationAuthenticate', 
    'OperationGetFeedContent', 'OperationGetMoreFeedContent', 
    'OperationMarkFeedRead', 
    'OperationMarkItemRead', 'OperationMarkItemUnread', 
    'OperationShareItem', 'OperationUnshareItem', 
    'OperationStarItem', 'OperationUnstarItem', 
]

from PyQt4.QtCore import Qt, QObject, QThread, QMutex
import itertools, sys, urllib2, socket
from collections import deque
from engine.signals import SIGNALS
from engine import network

class NotAuthenticatedError(Exception):pass


DEBUG = False
if DEBUG :
    def log(string):
        sys.stderr.write(string)
else:
    def log(string):
        pass

class Operation(object):
    """
    An operation managed by an OperationsManager and run by an OperationsThread
    This class must be overriden to change default values of fields:
        - name  : name of the operation, needed to find the opposite
        - type : "content" or "action" (for queue to add in)
        - opposite : name of the opposite operation to cancel (default None)
        - max_tries : max attempts to run the action (default 10)
        - max_same : max operations for the same action to run at the same time 
            (default None)
        - kill_same: kill operations with same name before trying to run it 
            (default False)
        - kill_opposite: kill opposite operations before trying to run it 
            (default True)
        - stop_on_http_errors: do not try again this operation if it returns an
            http error (default True)
    """

    
    id_counter = itertools.count(0) # counter for operation ids
    _by_id     = {}                 # all operation, by id
    
    @classmethod
    def get_by_id(cls, operation_id):
        """
        Return an operation by finding it with it's id
        """
        return Operation._by_id[operation_id]
    
    def __init__(self, **params):
        """
        Initialize fields of an operation.
        Params is a dictionnary for the action to run
        """
        self.id                   = Operation.id_counter.next()
        Operation._by_id[self.id] = self
        
        self.status   = 'new'
        self.nb_tries = 0
        
        self.name                = None
        self.type                = None
        self.opposite            = None
        self.max_tries           = None
        self.max_same            = None
        self.kill_same           = False
        self.kill_opposite       = True
        self.stop_on_http_errors = True

        # dictionnary for the action to run (typically have an "object" entry)
        self.params = params
        
        # when running we will keep a pointer to the thread
        self.thread = None

        # we store all errors
        self.errors   = []


    def ensure_param_is_present(self, param_name):
        """
        Ensure that a param is provided.
        Raise AssertionError if not
        """
        assert self.params and param_name in self.params, \
            "Parameter [%s] not provided" % param_name
        
    def get_identifier(self):
        """
        When an operation can have an opposite, the way to decide if two
        operations are opposites, is to check an identifier.
        Must be overriden if the behavior below is not wanted
        """
        try:
            return self.params['object'].id
        except:
            return None

    def do_action(self):
        """
        Run the action for the operation. 
        Must raise exceptions (if no exception, action is considered done)
        Must be overriden.
        """
        raise NotImplementedError
        
    def run(self, thread):
        """
        It's the main method of the operation. Will call the action (via 
        do_action) and manage exceptions, retries...
        """
        # check if we already have a thread:
        if self.thread:
            return
        self.thread = thread
        
        # work on this operation until it's really done or on error
        while True:
            try:
                # operation finished ? quit ! (btw it should not happen)
                if self.status in ('done', 'error'):
                    break
                # do action
                self.status = 'running'
                self.nb_tries += 1
                self.do_action()
            except NotAuthenticatedError, e:
                self.add_error(e)
                self.wait_for_authentication()
            except urllib2.HTTPError, e:
                # we have an http error
                self.add_error(e)
                if e.code == 401:
                    # it's 401 => need authentication
                    self.wait_for_authentication()
                else:
                    # it's not 401... a real error ?
                    if e.info().getheader('X-Reader-Google-Bad-Token'):
                        # but google say the auth is not good 
                        # => need authentication
                        self.wait_for_authentication()
                    elif self.stop_on_http_errors:
                        # it's a real error and we must stop on it
                        self.status = 'error'
                    else:
                        # it's a real error and we will continue after a delayfs
                        self.status = 'sleeping'
            except (urllib2.URLError, socket.error), e:
                # we have an urllib2 error... seems we are not connected !
                self.add_error(e)
                self.wait_for_network()
            except Exception, e:
                # we have an other exception... we continue
                self.add_error(e)
            else:
                self.status = 'done'

            # then we can check final status
            if self.status == 'done':
                # done => all it's ok, quit
                break
            elif self.max_tries and self.nb_tries >= self.max_tries:
                # we have tried at least max_tries
                self.status = 'error'
                break
            elif self.status == 'sleeping':
                # we want to sleep a little...
                self.thread.msleep(500)
                self.status = 'waiting'
            else:
                self.thread.msleep(500)
                self.status = 'waiting'
            
            # we are here because we need a retry, so nothing to do, the
            # while loop will do the stuff again
        
    def add_error(self, error):
        """
        Add the error in the errors list and print it on stderr
        """
        self.errors.append(error)
        log(self.str_error(error) + "\n")
                
    def __str__(self):
        """
        Get a readble representation of this operation
        """
        if self.max_tries:
            tries_str = "%d/%d" % (self.nb_tries, self.max_tries, )
        else:
            tries_str = self.nb_tries
        text = self.name
        identifier = self.get_identifier()
        if identifier:
            text = "%s for %s" % (self.name,  identifier)
        else:
            text = self.name
        return "Operation #%d [%s] (status=%s, tries=%s)" % (self.id, text, self.status, tries_str)
        
    def str_error(self, error):
        """
        Get a readable representation of this error
        """
        return "[op-error] %s: %s" % (self, error)
                        
    def wait_for_network(self):
        """
        We ask for network and we wait until we have it
        """
        self.status = 'waiting'
        self.thread.wait_for_network()
        self.nb_tries -= 1
        self.status = 'running'
        
    def wait_for_authentication(self):
        """
        We ask for a new authentication and we wait until it's done
        """
        self.status = 'waiting'
        self.thread.wait_for_authentication()
        self.nb_tries -= 1
        self.status = 'running'
        
    def is_opposite_of(self, operation):
        """"
        Check if this operation is the opposite of the one passed in parameters
        """
        if not self.opposite or not operation.opposite:
            return False
        if operation.opposite != self.name:
            return False
        return self.get_identifier() == operation.get_identifier()
        
    def is_same_as(self, operation):
        """
        Check if this operation is the same as the one passed in parameters
        """
        return self.name == operation.name \
            and self.get_identifier() == operation.get_identifier()

class OperationReconnect(Operation):
    """
    A special operation with "network" as type
    """
    def __init__(self, *args, **kwargs):
        """
        Set type="network" and max_same=1
        """
        super(OperationReconnect, self).__init__(*args, **kwargs)
        self.type     = "network"
        self.name     = 'reconnect'
        self.max_same = 1

    def do_action(self):
        """
        Try to obtain network. Wait until done.
        """
        network.wait()

class OperationAuthenticate(Operation):
    """
    A special operation with "authenticate" as type
    """
    def __init__(self, *args, **kwargs):
        """
        Set type="authenticate" and max_same=1
        Params : 
            * object : the account to authenticate
        """
        super(OperationAuthenticate, self).__init__(*args, **kwargs)
        self.type     = "authentication"
        self.name     = 'authenticate'
        self.max_same = 1
        self.max_tries = 1

    def do_action(self):
        """
        Try to authenticate to Google Reader.
        """
        self.params['object'].dist_authenticate()

class _OperationContent(Operation):
    """
    An operation with "content" as type.
    Must be overriden
    """
    def __init__(self, *args, **kwargs):
        """
        Set type = "content"
        """
        super(_OperationContent, self).__init__(*args, **kwargs)
        self.ensure_param_is_present('object')
        self.type = 'content'

class OperationGetAccountFeeds(_OperationContent):
    """
    An operation to get the feeds of google reader account
    """
    def __init__(self, *args, **kwargs):
        """
        Set name="get_account_feeds", max_tries=3, max_same=1
        Params : 
            * object : the account for which to get feeds
            * fetch_unread_content : If True (defaulft False), all the unread
                content for the account will be fetched when feeds fetching is
                done
        """
        super(OperationGetAccountFeeds, self).__init__(*args, **kwargs)
        self.name      = 'get_account_feeds'
        self.max_tries = 3
        self.max_same  = 1
        
    def do_action(self):
        """
        Get feeds for this account. And 
        """
        self.params['object'].dist_fetch_feeds()
        if self.params.get('fetch_unread_content', False):
            self.params['object'].fetch_unread_content()

class OperationGetFeedContent(_OperationContent):
    """
    An operation to get the content of a feed
    """
    def __init__(self, *args, **kwargs):
        """
        Set name="get_feed_content", kill_same=False, max_same=1.
        max_tries = 0 : run until it's successfull
        get_more_feed_content is set at opposite, with kill_opposite set
        to False to cancel this get_feed_content operation if 
        a get_more_feed_content is running.
        Params : 
            * object : the feed for which to get content
            * unread_only : if we just fetch the unread items (default False)
            * max_fetch : max item to fetch. Used to know if another fetch must
                be done right after this one (default None). Use -1 for 
                unlimited fetch (dangerous with unread_only=False)
        """
        super(OperationGetFeedContent, self).__init__(*args, **kwargs)
        self.name          = 'get_feed_content'
        self.opposite      = 'get_more_feed_content'
        self.max_tries     = 0
        self.max_same      = 1
        self.kill_same     = False
        self.kill_opposite = False

    def do_action(self):
        """
        Fetch feed content
        """
        self.params['object'].dist_fetch_content(
            unread_only=self.params.get('unread_only', False)
        )

class OperationGetMoreFeedContent(_OperationContent):
    """
    An operation to get more content for a feed
    """
    def __init__(self, *args, **kwargs):
        """
        Set name="get_more_feed_content", kill_same=False, max_same=1
        max_tries = 0 : run until it's successfull
        get_feed_content is set at opposite, with kill_opposite set
        to False to cancel this get_more_feed_content operation if 
        a get_feed_content is running.
        Params : 
            * object : the feed for which to get content
            * unread_only : if we just fetch the unread items (default False)
            * max_fetch : max item to fetch. Used to know if another fetch must
                be done right after this one (default None). Use -1 for 
                unlimited fetch (dangerous with unread_only=False)
            * continuation_id : the continuation param to use at Google Reader
                to get the next part of the list
        """
        super(OperationGetMoreFeedContent, self).__init__(*args, **kwargs)
        self.name          = 'get_more_feed_content'
        self.opposite      = 'get_feed_content'
        self.max_tries     = 0
        self.max_same      = 1
        self.kill_same     = False
        self.kill_opposite = False

    def do_action(self):
        """
        Fetch more feed content
        """
        self.params['object'].dist_fetch_more_content(
            unread_only     = self.params.get('unread_only', False), 
            continuation_id = self.params.get('continuation_id', None), 
        )

class _OperationAction(Operation):
    """
    An operation with "action" as type
    Must be overriden
    """
    def __init__(self, *args, **kwargs):
        """
        Set type="action" and max_same=1
        """
        super(_OperationAction, self).__init__(*args, **kwargs)
        self.ensure_param_is_present('object')
        self.type     = 'action'
        self.max_same = 1

class OperationMarkFeedRead(_OperationAction):
    """
    An operation to mark a feed as read
    """
    def __init__(self, *args, **kwargs):
        """
        Set name
        Params : 
            * object : the feed to mark as read
        """
        super(OperationMarkFeedRead, self).__init__(*args, **kwargs)
        self.name = 'mark_feed_read'

    def do_action(self):
        """
        Mark the feed as read
        """
        self.params['object'].dist_mark_as_read()

class OperationMarkItemRead(_OperationAction):
    """
    An operation to mark an item as read
    """
    def __init__(self, *args, **kwargs):
        """
        Set name and opposite
        Params : 
            * object : the item to mark as read
        """
        super(OperationMarkItemRead, self).__init__(*args, **kwargs)
        self.name     = 'mark_item_read'
        self.opposite = 'mark_item_unread'

    def do_action(self):
        """
        Mark the feed as read
        """
        self.params['object'].dist_mark_as_read()

class OperationMarkItemUnread(_OperationAction):
    """
    An operation to mark an item as unread
    """
    def __init__(self, *args, **kwargs):
        """
        Set name and opposite
        Params : 
            * object : the item to mark as unread
        """
        super(OperationMarkItemUnread, self).__init__(*args, **kwargs)
        self.name     = 'mark_item_read'
        self.opposite = 'mark_item_unread'

    def do_action(self):
        """
        Mark the feed as unread
        """
        self.params['object'].dist_mark_as_unread()

class OperationShareItem(_OperationAction):
    """
    An operation to share an item
    """
    def __init__(self, *args, **kwargs):
        """
        Set name and opposite
        Params : 
            * object : the item to share
        """
        super(OperationShareItem, self).__init__(*args, **kwargs)
        self.name     = 'share_item'
        self.opposite = 'unshare_item'

    def do_action(self):
        """
        Mark the feed as shared
        """
        self.params['object'].dist_share()

class OperationUnshareItem(_OperationAction):
    """
    An operation to unshare an item
    """
    def __init__(self, *args, **kwargs):
        """
        Set name and opposite
        Params : 
            * object : the item to unshare
        """
        super(OperationUnshareItem, self).__init__(*args, **kwargs)
        self.name     = 'unshare_item'
        self.opposite = 'share_item'

    def do_action(self):
        """
        Unmark the feed as shared
        """
        self.params['object'].dist_unshare()

class OperationStarItem(_OperationAction):
    """
    An operation to star an item
    """
    def __init__(self, *args, **kwargs):
        """
        Set name and opposite
        Params : 
            * object : the item to star
        """
        super(OperationStarItem, self).__init__(*args, **kwargs)
        self.name     = 'star_item'
        self.opposite = 'unstar_item'

    def do_action(self):
        """
        Mark the feed as stard
        """
        self.params['object'].dist_star()

class OperationUnstarItem(_OperationAction):
    """
    An operation to unstar an item
    """
    def __init__(self, *args, **kwargs):
        """
        Set name and opposite
        Params : 
            * object : the item to unstar
        """
        super(OperationUnstarItem, self).__init__(*args, **kwargs)
        self.name     = 'unstar_item'
        self.opposite = 'star_item'

    def do_action(self):
        """
        Unmark the feed as stard
        """
        self.params['object'].dist_unstar()
        
#class OperationGetItemContent(Operation):
#    """
#    An operation to get the item's content to read if offline
#    """
#    def __init__(self, *args, **kwargs):
#        """
#        Set type="item_content", name and max_same=1
#        """
#        super(_OperationAction, self).__init__(*args, **kwargs)
#        self.ensure_param_is_present('object')
#        self.type     = 'item_content'
#        self.max_same = 1
#        self.name = 'item_content'
#        
#    def do_action(self):
#        """
#        Get the item's content
#        """
#        # TODO: do stuff !
#        pass

class OperationsThread(QThread):
    """
    A thread for running operations. Has a spool as parent
    """
    def __init__(self, spool,  parent=None):
        super(OperationsThread, self).__init__(parent)
        self.spool = spool
        
    def ping(self):
        """
        A ping start a thread if it was not started. "run" method will 
        then be internally called
        """
        if not self.isRunning():
            self.start()
        
    def run(self):
        """
        Main method of the thread. Run while its spool can give him operations
        to run. Also send signals
        """
        while True:
            self.wait_ready()
            operation = self.spool.next()
            if not operation: break
            self.emit(SIGNALS['operation_started'], operation.id)
            operation.run(self)
            self.emit(SIGNALS['operation_ended'], operation.id)

    def wait_for_network(self):
        """
        We ask for network
        """
        self.spool.ask_for_network()
        self.wait_ready()
        
    def wait_for_authentication(self):
        """
        We ask for a new authentication
        """
        self.spool.ask_for_authentication()
        self.wait_ready()
        
    def wait_ready(self):
        """
        We wait until we are ready to continue (connected and authenticated)
        """
        while True:
            if self.spool.is_ready():
                break
            else:
                self.msleep(500)

class _OperationsSpool(QObject):
    """
    A spool of operations of a certain type. Can use many threads.
    """
    def __init__(self, parent):
        """
        Pprepare spools and threads
        Must be overriden to set :
            - type : one of "content", "action", "authentication", "network"
            - max_threads : max number of threads (default 1)
        """
        super(_OperationsSpool, self).__init__(parent)

        self.max_threads = 1
        self.threads     = [] # list of threads running operations
        self.mutex       = QMutex()
        
        self.spool   = deque() # list of remaining operations
        self.running = []      # list of running operations
        self.done    = []      # list of finished operations
        self.errors  = []      # list of failed operations
        self.waiting = deque() # list of operations not yet added to the spool
        
    def count_all(self):
        """
        Return a hash with count of operations for each list in this spool
        """
        result = {}
        for type in ('spool', 'running', 'done', 'errors', 'waiting', ):
            result[type] = len(getattr(self, type))
        return result
        
    def count_running(self):
        """
        Count "alive" operations : spool + running + waiting
        """
        by_type = self.count_all()
        return by_type['spool'] + by_type['running'] + by_type['waiting']
        
    def add(self, operation):
        """
        Add an operation to the waiting spool
        """
        self.waiting.append(operation)
        self.check_waiting_list()
        
    def check_waiting_list(self):
        """
        This method will check conditions about the operation
        before to put it in the spool queue (max_same, kill_same, opposites...)
        Thi method is threadsafe (mutex.lock is here to ensure that only one
        waiting operation is checked at a time)
        """
        self.mutex.lock()
        try:
            # get operation
            operation = self.waiting.popleft()

            # check operations specificities
            can_add, to_remove = self._test_opposite(operation)
            for op in to_remove:
                op.status = 'rejected'
                self.spool.remove(op)
            if can_add:
                can_add, to_remove = self._test_same(operation)
                for op in to_remove:
                    op.status = 'rejected'
                    self.spool.remove(op)

            # finally add the operation to the spool only if we can add
            # the operation
            if can_add:
                self.spool.append(operation)
                self.ping_threads()
            else:
                operation.status = 'rejected'
        finally:
            self.mutex.unlock()
            
    def _test_opposite(self, operation):
        """
        If the operation has an opposite name, this method check opposites in 
        the spool. If an opposite is found and the kill_opposite flag is True,
        then the opposite operation is removed from the spool, but if the flag
        is False, then the current operation is cancelled.
        """
        to_remove = []
        can_add   = True

        if operation.opposite:
            for op in self.spool:
                if op.is_opposite_of(operation):
                    if operation.kill_opposite:
                        to_remove.append(op)
                    else:
                        can_add = False
        return can_add, to_remove
                
    def _test_same(self, operation):
        """
        If the operation has a positive max_same, this method will check for
        same operations in the spool and if at least one, return False (and an
        empty list of operations to remove). 
        Else if we have a kill_same, we check for same operations in the spool
        and return True (operation still valid) and the list of removals
        """
        to_remove = []
        can_add   = True
        
        # check max_same
        if operation.max_same:
            count_same = 0
            for op in self.spool:
                if op.is_same_as(operation):
                    count_same += 1
                    if count_same >= operation.max_same:
                        can_add = False
                        break

        # check max_same
        elif operation.kill_same:
            to_remove = []
            for op in self.spool:
                if op.is_same_as(operation):
                    to_remove.append(op)
                
        return can_add, to_remove
            
    def next(self):
        """
        Return the next operation to run, remove it from the spool queue,
        and move it to the running one.
        Will be called by the next thread which has finished working on its
        previous operation. This method is threadsafe (mutex.lock is here to 
        ensure only one thread at a time can claim a operation)
        """
        self.mutex.lock()
        try:
            operation = self.spool.popleft()
            self.running.append(operation)
            return operation
        except:
            return None
        finally:
            self.mutex.unlock()

    def ask_for_network(self):
        """
        We ask for network
        """
        self.parent().ask_for_network()
        
    def ask_for_authentication(self):
        """
        We ask for a new authentication
        """
        self.parent().ask_for_authentication()
        
    def is_ready(self):
        """
        Check if the spool is ready to work (we are both connected and
        authenticated)
        """
        return self.parent().is_ready()
        
    def ping_threads(self):
        """
        Ping all threads to let them check if new operations are available
        in the spool. A new thread is created if needed (and possible)
        """
        one_available = False
        for thread in self.threads:
            if not thread.isRunning():
                one_available = True
            thread.ping()
                
        if not one_available and len(self.threads) < self.max_threads:
            thread = OperationsThread(spool=self)
            QObject.connect(thread, SIGNALS['operation_started'], self.operation_started, Qt.QueuedConnection)
            QObject.connect(thread, SIGNALS['operation_ended'], self.operation_ended, Qt.QueuedConnection)
            self.threads.append(thread)
            thread.ping()
            
    def operation_started(self, operation_id):
        """
        Forward the "operation_started" from the spool to the operations manager
        """
        log("[op-start] %s\n" % Operation.get_by_id(operation_id))
        operation = Operation.get_by_id(operation_id)
        self.parent().emit(SIGNALS['%s_started' % operation.name],  operation_id)
        self.parent().emit(SIGNALS['operation_started'], operation_id)
            
    def operation_ended(self, operation_id):
        """
        Forward the "operation_ended" from the spool to the operations manager
        """
        # get the corresponding operation
        operation = Operation.get_by_id(operation_id)
        # update the spool
        self.running.remove(operation)
        if operation.status == 'done':
            self.done.append(operation)
        else:
            self.errors.append(operation)
        # alert that an operation has finished
        log("[op-end] %s\n" % operation)
        self.parent().emit(SIGNALS['operation_ended'], operation_id)        
        # then alert for this specific operation
        status = 'done'
        operation = Operation.get_by_id(operation_id)
        if operation.status != 'done':
            status = 'error'
        self.parent().emit(SIGNALS['%s_%s' % (operation.name,  status)],  operation_id)
        

class ContentSpool(_OperationsSpool):
    """
    A spool for managing operations with type "content"
    """
    def __init__(self, *args, **kwargs):
        """
        Set type to "content" and max_threads to 2
        """
        super(ContentSpool, self).__init__(*args, **kwargs)
        self.type = 'content'
        self.max_threads = 2

class ActionSpool(_OperationsSpool):
    """
    A spool for managing operations with type "action"
    """
    def __init__(self, *args, **kwargs):
        """
        Set type to "action" and max_threads to 2
        """
        super(ActionSpool, self).__init__(*args, **kwargs)
        self.type = 'action'
        self.max_threads = 2

class AuthenticationSpool(_OperationsSpool):
    """
    A spool for managing operations with type "authentication"
    """
    def __init__(self, *args, **kwargs):
        """
        Set type to "authentication"
        """
        super(AuthenticationSpool, self).__init__(*args, **kwargs)
        self.type = 'authentication'
        
    def is_ready(self):
        """
        Check if the spool is ready to work (we are connected)
        """
        return self.parent().is_connected

class NetworkSpool(_OperationsSpool):
    """
    A spool for managing operations with type "network". Only one should be
    created, which can be retrived by NetworkSpool.get_current()
    """
    
    # we just have one network spool for all operations managers
    _current_network_spool = None
    
    @classmethod
    def get_current(cls):
        """
        Return the current network spool used (or None)
        """
        return cls._current_network_spool
    
    def __init__(self, *args, **kwargs):
        """
        Set type to "network"
        """
        super(NetworkSpool, self).__init__(*args, **kwargs)
        self.__class__._current_network_spool = self
        self.type = 'network'
        
    def is_ready(self):
        """
        For this spool, we are always ready
        """
        return True


class OperationsManager(QObject):
    """
    The operations manager will manage all asynchronous operations 
    about Google Reader.
    Callbacks is None or a hash with operations signal as key (like 
    "fetch_feed_content_done", or "authenticate_error", and as value, a callback
    which can take as "operation" parameter the operation which has emitted the
    signal
    """

    def __init__(self, account, callbacks=None):
        """
        Create the OperationsManager, inialize all things (signals, spools...)
        """
        super(OperationsManager, self).__init__(parent=None)
        
        # an operation manager is for a specified account
        self.account = account
        
        # create needed spools
        self.spools = {
            'content':        ContentSpool(self), 
            'action':         ActionSpool(self), 
            'authentication': AuthenticationSpool(self), 
            'network':        NetworkSpool.get_current() or NetworkSpool(self),
        }
        
        # default connected and authenticated. Real status will be managed
        # by automatically created operation
        self.is_connected       = True
        self.is_authenticated   = True
        
        # connect to signals
        QObject.connect(self, SIGNALS["reconnect"], self.reconnect, Qt.QueuedConnection)        
        QObject.connect(self, SIGNALS["reconnect_done"], self._reconnect_done, Qt.QueuedConnection)
        QObject.connect(self, SIGNALS["authenticate"], self.authenticate, Qt.QueuedConnection)
        QObject.connect(self, SIGNALS["authenticate_error"], self._authenticate_error, Qt.QueuedConnection)
        QObject.connect(self, SIGNALS["authenticate_done"], self._authenticate_done, Qt.QueuedConnection)

        # connect signals asked by owner of this operation manager
        self.callbacks = callbacks
        if callbacks is not None:
            for op_signal in callbacks.keys():
                QObject.connect(self, SIGNALS[op_signal], self._signal_callback, Qt.QueuedConnection)
                    
    def _signal_callback(self, operation_id):
        """
        Redirect signals to callbaks to the owner of this operation manager
        """
        operation = Operation.get_by_id(operation_id) 
        signal = operation.name
        if operation.status == 'done':
            signal += '_done'
        else:
            signal += '_error'
        if signal in self.callbacks:
            self.callbacks[signal](operation)

    def is_ready(self):
        """
        Check if we are ready to work (we are both connected and
        authenticated)
        """
        return self.is_connected and self.is_authenticated
        
    def count_all(self):
        """
        Return a count for all operation list in all spools
        """
        return dict((spool_name, spool.count_all()) for spool_name, spool in self.spools.iteritems())
        
    def count_running(self):
        """
        Sum "alive" operations in each spools
        """
        return sum([spool.count_running() for spool in self.spools.values()])

    def add(self, operation):
        """
        Add an operation to the manager, by putting it in the appropriate spools
        """
        if isinstance(operation, OperationAuthenticate):
            self.is_authenticated = False
        self.spools[operation.type].add(operation)

    def ask_for_network(self):
        """
        We ask for network
        """
        self.is_connected = False
        self.emit(SIGNALS['reconnect'])

    def reconnect(self):
        """
        Create a new "reconnect" operation
        """
        self.is_connected = False
        self.add(OperationReconnect())
        
    def _reconnect_done(self, operation_id):
        """
        Called when the network is on again
        """
        self.is_connected = network.available
        
    def ask_for_authentication(self):
        """
        We ask for a new authentication
        """
        self.is_authenticated = False
        self.emit(SIGNALS['authenticate'])

    def authenticate(self):
        """
        Ask for a new authentication
        """
        self.is_authenticated = False
        self.account.authenticate()
        
    def _authenticate_error(self, operation_id):
        """
        Called when the authentication just failed
        """
        self.is_authenticated = False
        
        
    def _authenticate_done(self, operation_id):
        """
        Called when the authentication is correctly done
        """
        self.is_authenticated = True
