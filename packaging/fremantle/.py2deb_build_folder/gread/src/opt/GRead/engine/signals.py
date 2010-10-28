# -*- coding: utf-8 -*-

"""
A module to regroup and initialize all signals.
"""

from PyQt4.QtCore import SIGNAL

# list of all signals managed by GRead
SIGNALS = dict((name, SIGNAL(name)) for name in (
    # name                   # emitted by           # called when...
    #---------------------------------------------------------------------------
    'settings_updated',              # controller           # settings are updated
    
    'operation_started',             # OperationsThread+operations_manager     # an operation has just started
    'operation_ended',               # OperationsThread+operations_manager     # an operation done or failed
    
    'reconnect',                     # operations_manager   # a reconnect is needed
    'reconnect_started',             # operations_manager   # a reconnect has just started
    'reconnect_done',                # operations_manager   # a reconnect is done
    'reconnect_error',               # operations_manager   # a reconnect has failed (should'nt happen)
    
    'authenticate',                  # operations_manager   # an authentication is needed
    'authenticate_started',          # operations_manager   # an authentication has just started
    'authenticate_done',             # operations_manager   # an authentication is done
    'authenticate_error',            # operations_manager   # an authentication failed
    
    'get_account_feeds',             # operations_manager   # account's feeds must be retrieved
    'get_account_feeds_started' ,    # operations_manager   # account's feeds retrieval has just started
    'get_account_feeds_done',        # operations_manager   # account's feeds were retrieved
    'get_account_feeds_error',       # operations_manager   # account's feeds failed to be retrieved
    
    'get_feed_content',              # operations_manager   # a feed's content must be retrieved
    'get_feed_content_started' ,     # operations_manager   # a feed's content retrieval has just started
    'get_feed_content_done',         # operations_manager   # a feed's content was retrieved
    'get_feed_content_error',        # operations_manager   # a feed's content failed to be retrieved
    
    'get_more_feed_content',         # operations_manager   # more content of a feed  must be retrieved
    'get_more_feed_content_started' ,# operations_manager   # more content of a feed  retrieval has just started
    'get_more_feed_content_done',    # operations_manager   # more content of a feed  was retrieved
    'get_more_feed_content_error',   # operations_manager   # more content of a feed failed to be retrieved

    'mark_feed_read',                # operation_manager    # a feed must be marked as read
    'mark_feed_read_started',        # operations_manager   # a feed marking as read has just started
    'mark_feed_read_done',           # operation_manager    # a feed was marked as read
    'mark_feed_read_error',          # operation_manager    # a feed failed to be marked as read

    'mark_item_read',                # operation_manager    # a item must be marked as read
    'mark_item_read_started',        # operations_manager   # a item marking as read has just started
    'mark_item_read_done',           # operation_manager    # a item was marked as read
    'mark_item_read_error',          # operation_manager    # a item failed to be marked as read

    'mark_item_unread',              # operation_manager    # a item must be marked as unread
    'mark_item_unread_started',      # operations_manager   # a item marking as unread has just started
    'mark_item_unread_done',         # operation_manager    # a item was marked as unread
    'mark_item_unread_error',        # operation_manager    # a item failed to be marked as unread

    'share_item',                    # operation_manager    # a item must be marked as shared
    'share_item_started',            # operations_manager   # a item marking as shared has just started
    'share_item_done',               # operation_manager    # a item was marked as shared
    'share_item_error',              # operation_manager    # a item failed to be marked as shared

    'unshare_item',                  # operation_manager    # a item must be marked as not shared
    'unshare_item_started',          # operations_manager   # a item marking as unshared has just started
    'unshare_item_done',             # operation_manager    # a item was marked as not shared
    'unshare_item_error',            # operation_manager    # a item failed to be marked as not shared

    'star_item',                     # operation_manager    # a item must be marked as starred
    'star_item_started',             # operations_manager   # a item marking as starred has just started
    'star_item_done',                # operation_manager    # a item was marked as starred
    'star_item_error',               # operation_manager    # a item failed to be marked as starred

    'unstar_item',                   # operation_manager    # a item must be marked as not starred
    'unstar_item_started',           # operations_manager   # a item marking as unstarred has just started
    'unstar_item_done',              # operation_manager    # a item was marked as not starred
    'unstar_item_error',             # operation_manager    # a item failed to be marked as not starred
))
