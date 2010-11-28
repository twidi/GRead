
from PyQt4.QtSql import *
from PyQt4.QtCore import *

from random import randint

from engine import DEBUG, log
from ..storage import *
import queries

class DBUpgradeCannotBeDone(StorageError): pass

class Storage(BaseStorage):
	"""
	Storage backend using a sqlite database.
	"""

	def __init__(self, *args, **kwargs):
		super(Storage, self).__init__(*args, **kwargs)
		self._db = None

	def configure(self, params):
		"""
		Check if these params are ok : path
		"""
		super(Storage, self).configure(params)
		if not self.conf.get('path'):
			raise StorageImproperlyConfigured('DB path not provided')
		self.configured = True

	def init(self):
		"""
		Initialize the connextion, open it and check integrity of the db
		"""
		super(Storage, self).init()
		self._db = QSqlDatabase.addDatabase("QSQLITE")
		self._db.setDatabaseName(self.conf['path'])
		if self._db.open():
			self.check_integrity()
			self.initialized = True
		else:
			raise StorageCannotBeInitialized(self.db_error(self._db.lastError()))

	def end(self):
		"""
		Enf of connection : we need to close sthe qlite connection
		"""
		self._db.close()
		super(Storage, self).end()

	def db_error(self, error, prefix=None):
		"""
		Compose a string error from a sql error and a prefix
		"""
		str_db = "%d / %s / %s" % (error.number(), error.driverText(), error.databaseText())
		if prefix:
			return "%s [%s]" % (prefix, str_db)
		else:
			return str_db

	def check_integrity(self):
		"""
		Check the integrity of all tables, and create missing tables and 
		add/update/remove fields if needed
		"""
		for table_name in queries.TABLES:
			table = queries.TABLES[table_name]

			# create table if not exists
			try:
				query = queries.query(queries.create_table_query(table))
				if not query.isActive():
					raise Exception('Table "%s" cannot be created' % table_name)

			except Exception, e:
				str_e = str(e)
				try:
					last_error = query.lastError()
					if last_error and last_error.isValid():
						str_e = self.db_error(last_error, str_e)
				except:
					pass
				raise DBUpgradeCannotBeDone(str_e)

			# check fields to update/add/remove
			try:
				query = queries.query('pragma table_info(%s)' % table_name)
				db_fields = {}
				while query.next():
					name    = str(query.value(1).toString())
					type    = str(query.value(2).toString())
					null    = not query.value(3).toBool()
					default = str(query.value(4).toString())
					db_fields[name] = (name, type, null, default)

				fields_to_update = []
				fields_to_add    = []
				fields_to_remove = []
				for field_name, field in table['fields'].iteritems():
					if field_name in db_fields:
						if db_fields[field_name] != field:
							fields_to_update.append(field_name)
					else:
						fields_to_add.append(field_name)
				for field_name in db_fields:
					if field_name not in table['fields']:
						fields_to_remove.append(field_name)

				if fields_to_update or fields_to_add or fields_to_remove:

					if DEBUG:
						log_str = 'Table "%s" is going to be updated :'
						if fields_to_add:
							log_str += ' add(%s)' % (', '.join(fields_to_add))
						if fields_to_remove:
							log_str += ' remove(%s)' % (', '.join(fields_to_remove))
						if fields_to_update:
							log_str += ' update(%s)' % (', '.join(fields_to_update))
						log(log_str)

					# add columns
					if fields_to_add:
						fields = [table['fields'][field_name] for field_name in fields_to_add]
						query = queries.query(queries.alter_table_add_fields_query(table, fields))
						if not query.isActive():
							raise Exception('Table "%s" cannot be updated' % table_name)

					# remove or update columns by creating a new table
					if fields_to_remove or fields_to_update:
						try:
							self._db.transaction()
	
							# create the new table
							new_table_name = '%s_new%d' % (table_name, randint(1, 1000))
							new_table = {
								'fields': table['fields'],
								'pk':     table['pk'],
							}
							new_table['name'] = new_table_name
							query = queries.query(queries.create_table_query(new_table))
							if not query.isActive():
								raise Exception('Table "%s" cannot be updated' % table_name)
	
							# get fields order
							query = queries.query('pragma table_info(%s)' % table_name)
							ordered_fields = []
							while query.next():
								ordered_fields.append(str(query.value(1).toString()))
	
							# copy data
							query = queries.query(queries.insert_into_select_query(
								table,
								new_table,
								ordered_fields,
							))
							if not query.isActive():
								raise Exception('Table "%s" cannot be updated' % table_name)
	
							# drop old table
							query = queries.query(queries.drop_table_query(table))
							if not query.isActive():
								raise Exception('Table "%s" cannot be updated' % table_name)

							# rename new table
							query = queries.query(queries.rename_table_query(new_table, table['name']))
							if not query.isActive():
								raise Exception('Table "%s" cannot be updated' % table_name)

						except Exception, e:
							self._db.rollback()
							raise e

						else:
							self._db.commit()

			except Exception, e:
				str_e = str(e)
				try:
					last_error = query.lastError()
					if last_error and last_error.isValid():
						str_e = self.db_error(last_error, str_e)
				except:
					pass
				raise DBUpgradeCannotBeDone(str_e)

