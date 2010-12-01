# -*- coding: utf-8 -*-

import os

from engine import settings, log
from views import view_mode

from PyQt4.QtCore import QThread


# Global storage variable
Storage = None
STORAGE_ENABLED = True

homedir = os.path.expanduser("~")

# default gread directory
GREAD_DIR = os.path.join(homedir, 'GRead')

# specific directories
if view_mode == 'maemo5':
    path = os.path.join(homedir, 'MyDocs')

# create gread directory
if not os.path.exists(GREAD_DIR):
    try:
        os.makedirs(GREAD_DIR)
    except Exception, e:
        log(str(e))
        STORAGE_ENABLED = False

# add default settings
settings.add_defaults({
    'storage' : {
        'enabled':  True,
        'base_dir': GREAD_DIR,
    },
})

class StorageError(Exception): pass
class StorageIsDisabled(StorageError): pass
class StorageImproperlyConfigured(StorageError): pass
class StorageNotInitialized(StorageError): pass
class StorageCannotBeInitialized(StorageError): pass
class ObjectError(StorageError): pass
class ObjectNotFound(ObjectError): pass
class CannotAddObject(ObjectError): pass
class CannotReadObject(ObjectError): pass
class CannotUpdateObject(ObjectError): pass
class CannotDeleteObject(ObjectError): pass

class BaseStorage(object):
    """
    Base model for all storage backends.
    """
    
    def __init__(self):
        if settings.get('storage', 'enabled') != STORAGE_ENABLED:
            settings.set('storage', 'enabled', STORAGE_ENABLED)
        self.name = 'base'

        self.conf = {}
        self.configured  = False
        self.initialized = False

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

    def end(self):
        """
        Close the storage
        """
        self.initialized = False

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

    def find_objects(self, object_type, query, operator='and'):
        """
        Find all objects of a certain type regarding specified query.
        Actually query is a dict with fields as keys and values to search for as values.
        All fields are combined with an operator which can be either "and" (default) or "or"
        Return a list (empty list if no object found)
        """
        self.assert_ready()
        return []

    def find_and_update_objects(self, object_type, data, query, operator='and'):
        """
        Find all objects of a certain type regarding specified query (see "find_objects") and update them with the specified data (see "update_objects")
        """
        self.assert_ready()
        objects = self.find_objects(self, object_type, query, operator)
        ids = [obj['id'] for obj in objects]
        self.update_objects(object_type, ids, data)

    def find_and_delete_objects(self, object_type, query, operator='and'):
        """
        Find all objects of a certain type regarding specified query (see "find_objects") and delete them)
        """
        self.assert_ready()
        objects = self.find_objects(self, object_type, query, operator)
        ids = [obj['id'] for obj in objects]
        self.delete_objects(object_type, ids)

