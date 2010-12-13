# -*- coding: utf-8 -*-

import inspect
from engine import settings, log

from storage import STORAGE_ENABLED
from storage.exceptions import *
from storage.operations import StorageOperation
from storage.signals import SIGNALS


from PyQt4.QtCore import Qt, QThread, QObject

class BaseStorage(QThread):
    """
    Base model for all storage backends.
    """
    
    def __init__(self, *args, **kwargs):
        super(BaseStorage, self).__init__(*args, **kwargs)

        if settings.get('storage', 'enabled') != STORAGE_ENABLED:
            settings.set('storage', 'enabled', STORAGE_ENABLED)
        self.name = 'base'

        self.conf = {}
        self.configured  = False
        self.initialized = False

        self. method_args = {}

        if not STORAGE_ENABLED:
            raise StorageIsDisabled

    def assert_ready(self):
        """
        Check if the storage is configured and initialized
        """
        if not self.configured:
            raise StorageImproperlyConfigured
        elif not self.initialized:
            raise StorageNotInitialized

    def configure(self, params=None):
        """
        Configuration to be used by the backend
        The storage must set self.configured to True
        If params is None, use settings
        """
        if params is None:
            self.conf = settings.get_group('storage_%s' % self.name)
        else:
            self.conf = params

    def init(self):
        """
        Init the storage
        The storage must set self.initialized to True
        """
        if not self.configured:
            raise StorageImproperlyConfigured

    def run(self):
        """
        Enter the thread endless loop.
        Start by call init, and then wait for signals
        """
        if not self.initialized:
            self.init()
            if not self.initialized:
                raise StorageCannotBeInitialized
            self.init_signals()
        # call exec and return when quit is called
        super(BaseStorage, self).run()

    def end(self):
        """
        Close the storage
        """
        self.initialized = False
        self.quit()

    def manage_unavailability(self):
        """
        If a StorageTemporarilyNotAvailable exception is raised, this
        method will be called. Does nothing by default
        """
        pass

    def wanted_args(self, method):
        """
        Return arguments wanted by a method, excluding self, as a dict with
        arg name as value and required status as value
        Call inspect.getargspec but use a cache to avoid 
        multiple calls for same methods
        """
        if not method in self.method_args:
            args_spec = inspect.getargspec(method)
            args = dict((arg, True) for arg in args_spec.args)
            del args['self']
            for arg in args_spec[len(args_spec.args)-len(args_spec.defaults):]:
                args[arg] = False
            self.method_args[method] = args
        return self.method_args[method]

    def connect_signal(self, signal, method):
        """
        Wrapper to add a signal for the thread
        """
        QObject.connect(self, SIGNALS[signal], method, Qt.QueuedConnection)

    def init_signals(self):
        """
        Init all signal that will be used by the thread
        """
        self.connect_signal('operation_added', self.operation_added)
        self.connect_signal('operation_started', self.operation_started)
        self.connect_signal('operation_ended', self.operation_ended)

    def add_operation(self, name, params):
        """
        Add an operation to be executed by the Storage thread.
        """
        operation = StorageOperation(name, params)
        self.emit(SIGNALS['operation_added'], operation.id)
        return operation

    def operation_added(self, operation_id):
        operation = Operation.get_by_id(operation_id)
        self.emit(SIGNALS['operation_started'], operation.id)
        operation.run(self)
        self.emit(SIGNALS['operation_ended'], operation.id)

    def operation_started(self, operation_id):
        operation = Operation.get_by_id(operation_id)
        log("s-op-start] %s" % operation)
        self.emit(SIGNALS['%s_started' % operation.name], operation_id)

    def operation_ended(self, operation_id):
        operation = Operation.get_by_id(operation_id)
        log("s-op-end] %s" % operation)
        self.emit(SIGNALS['%s_done' % operation.name], operation_id)

    def add_object(self, object_type, data):
        """
        Add an object of a certain type, with some data (a dict)
        Return the pk of the new entry
        Raise CannotAddObject if it fails
        """
        self.assert_ready()

    def read_object(self, object_type, id):
        """
        Read the object of a certain type with the specified id
        Return a dict
        Raise CannotReadObject if it fails and ObjectNotFound if not found
        """
        self.assert_ready()

    def update_object(self, object_type, id, data):
        """
        Update the object of a certain type with the specified id, with the given data (a dict field=>value)
        Raise CannotUpdateObject if it fails and ObjectNotFound if not found
        """
        self.assert_ready()

    def delete_object(self, object_type, id):
        """
        Delete the object of a certain type with the specified id
        Raise CannotDeleteObject if it fails and ObjectNotFound if not object is not found
        """
        self.assert_ready()

    def add_objects(self, object_type, objects):
        """
        Add many objects of the same type. 
        "objects" is a list of dicts (one dict per object to add)
        Return a list with one entry for each object: the id if ok, and the exception if it fails
        """
        self.assert_ready()
        ids = []
        for data in objects:
            try:
                ids.append(self.add_object(object_type, data))
            except Exception, e:
                ids.append(e)
        return ids

    def read_objects(self, object_type, ids):
        """
        Read many objects of the same type, with the given ids
        Return a list with one entry for each id: the result if ok, and the exception if it fails
        """
        self.assert_ready()
        objects = []
        for id in ids:
            try:
                objects.append(self.read_object(object_type, id))
            except Exception, e:
                objects.append(e)
        return objects

    def update_objects(self, object_type, ids, data):
        """
        Update many objects of the same type by setting same data (see "update_object") for all ids.
        Return a list with one entry for each id: None if ok, and the exception if it fails
        """
        self.assert_ready()
        results = []
        for id in ids:
            try:
                self.update_object(object_type, id, data)
                results.append(None)
            except Exception, e:
                results.append(e)
        return results

    def delete_objects(self, object_type, ids):
        """
        Delete many objects of the same type
        Return a list with one entry for each id: None if ok, and the exception if it fails
        """
        self.assert_ready()
        results = []
        for id in ids:
            try:
                self.delete_object(object_type, id)
                results.append(None)
            except Exception, e:
                results.append(e)
        return results

    def find_objects(self, object_type, filter, operator='and', limit=None, offset=None):
        """
        Find all objects of a certain type regarding specified filter.
        Actually filter is a dict with fields as keys and values to search for as values.
        All fields are combined with an operator which can be either "and" (default) or "or"
        Return a list (empty list if no object found)
        """
        self.assert_ready()
        return []

    def find_and_update_objects(self, object_type, data, filter, operator='and'):
        """
        Find all objects of a certain type regarding specified filter (see "find_objects") and update them with the specified data (see "update_objects")
        """
        self.assert_ready()
        objects = self.find_objects(self, object_type, filter, operator)
        ids = [obj['id'] for obj in objects]
        self.update_objects(object_type, ids, data)

    def find_and_delete_objects(self, object_type, filter, operator='and'):
        """
        Find all objects of a certain type regarding specified filter (see "find_objects") and delete them)
        """
        self.assert_ready()
        objects = self.find_objects(self, object_type, filter, operator)
        ids = [obj['id'] for obj in objects]
        self.delete_objects(object_type, ids)

