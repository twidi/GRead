class StorageError(Exception): pass
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
		self.conf = {}
		self.configured  = False
		self.initialized = False

	def assert_ready(self):
		"""
		Check if the storage is configured and initialized
		"""
		if not self.configured:
			raise StorageImproperlyConfigured
		elif not self.initialized:
			raise StorageNotInitialized

	def configure(self, params):
		"""
		Configuration to be used by the backend
		The storage must set self.configured to True
		"""
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

	def __del__(self):
		"""
		Destructor : ask to close the storage
		"""
		if self.initialized:
			self.end()

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
		"""
		self.assert_ready()
		for data in objects:
			self.add_object(object_type, data)

	def read_objects(self, object_type, ids):
		"""
		Read many objects of the same type, with the given ids
		"""
		self.assert_ready()
		objects = []
		for id in ids:
			objects.append(self.read_object(object_type, id))
		return objects

	def update_objects(self, object_type, ids, data):
		"""
		Update many objects of the same type by setting same data (see "update_object") for all ids.
		"""
		self.assert_ready()
		for id in ids:
			self.update_object(object_type, id, data)

	def delete_objects(self, object_type, ids):
		"""
		Delete many objects of the same type
		"""
		self.assert_ready()
		for id in ids:
			self.delete_object(object_type, id)

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

