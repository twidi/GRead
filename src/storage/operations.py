# -*- coding: utf-8 -*-

import itertools
from engine import log
from storage.exceptions import *

class StorageOperation(object):
    """
    An operation to be executed by the Storage thread
    TODO : create a common ancestor with engine.operations.Operation
    """
    id_counter = itertools.count(0) # counter for operation ids
    _by_id     = {}                 # all operation, by id

    def __init__(self, name, params, max_tries = 1):
        self.id                          = StorageOperation.id_counter.next()
        StorageOperation._by_id[self.id] = self

        # operation specific fields
        self.status    = 'new'
        self.max_tries = max_tries
        self.nb_tries  = 0

        # action specific fields
        self.name   = name
        self.params = params
        
        # the result will be stored here
        self.result = None
        
        # when running we will keep a pointer to the thread
        self.thread = None

        # we store all errors
        self.errors = []

    def ensure_param_is_present(self, param_name):
        """
        Ensure that a param is provided.
        Raise AssertionError if not
        """
        assert self.params and param_name in self.params, \
            "Parameter [%s] not provided" % param_name

    def get_identifier(self):
        """
        Currently only check if we have a "id" field in params and return it
        """
        return self.params.get('id', None)

    def add_error(self, error):
        """
        Add the error in the errors list and print it on stderr
        """
        self.errors.append(error)
        log(self.str_error(error))

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
        return "Storage Operation #%d [%s] (status=%s, tries=%s)" % (self.id, text, self.status, tries_str)
        
    def str_error(self, error):
        """
        Get a readable representation of this error
        """
        return "[s-op-error] %s: %s" % (self, error)

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
            except StorageTemporarilyNotAvailable:
                self.status = 'waiting'
                self.nb_tries -= 1
                self.thread.manage_unavailability()
                self.status = 'running'
            except Exception, e:
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
            else:
                self.thread.msleep(500)
                self.status = 'waiting'

    def do_action(self):
        """
        Run the action for the operation.
        """
        # get action
        action = getattr(self.thread, self.name)
        # check arguments
        wanted_args = self.thread.wanted_args(action)
        for arg, required in wanted_args.iteritems():
            if required:
                self.ensure_param_is_present(arg)
        # prepare arguments
        params = dict((arg, self.params[arg]) for arg in wanted_args if arg in self.params)
        # do action
        self.result = action(**params)

