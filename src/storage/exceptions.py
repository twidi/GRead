# -*- coding: utf-8 -*-

class StorageError(Exception): pass
class StorageIsDisabled(StorageError): pass
class StorageImproperlyConfigured(StorageError): pass
class StorageNotInitialized(StorageError): pass
class StorageCannotBeInitialized(StorageError): pass
class StorageTemporarilyNotAvailable(StorageError): pass
class ObjectError(StorageError): pass
class ObjectNotFound(ObjectError): pass
class CannotAddObject(ObjectError): pass
class CannotReadObject(ObjectError): pass
class CannotUpdateObject(ObjectError): pass
class CannotDeleteObject(ObjectError): pass
