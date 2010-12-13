# -*- coding: utf-8 -*-

from PyQt4.QtSql import *
from PyQt4.QtCore import *

from random import randint
import os

from engine import DEBUG, log, settings
from storage import GREAD_DIR
from storage.exceptions import *
from storage.base import BaseStorage
import queries

# add default settings
settings.add_defaults({
    'storage_sqlite': {
        'path': os.path.join(GREAD_DIR, 'gread.sqlite'),
    },
})

class DBUpgradeCannotBeDone(StorageError): pass


class Storage(BaseStorage):
    """
    Storage backend using a sqlite database.
    """

    def __init__(self, *args, **kwargs):
        super(Storage, self).__init__(*args, **kwargs)
        self.name = 'sqlite'
        self._db = None
        self._prepared_queries = {}

    def configure(self, params=None):
        """
        Configuration to be used by the backend
        The storage must set self.configured to True
        If params is None, use settings
        sqlite : Check if these params are ok : path
        """
        super(Storage, self).configure(params)
        if not self.conf.get('path'):
            raise StorageImproperlyConfigured('DB path not provided')
        self.configured = True

    def init(self):
        """
        Init the storage
        The storage must set self.initialized to True
        sqlite : Initialize the connextion, open it and check integrity of the db
        """
        super(Storage, self).init()
        if self.reconnect():
            self.check_integrity()
            self.prepare_queries()
            self.initialized = True
        else:
            raise StorageCannotBeInitialized(self.db_error(self._db.lastError()))

    def reconnect(self):
        """
        Connect/Reconnect the DB
        """
        self._db = QSqlDatabase.addDatabase("QSQLITE")
        self._db.setDatabaseName(self.conf['path'])
        return self._db.open()

    def manage_unavailability(self):
        """
        Try to reconnect the DB
        """
        nb_tries = 0
        while nb_tries < 5:
            nb_tries += 1
            if self.reconnect():
                break
            self.msleep(500)
        if nb_tries >= 5:
            self.msleep(2000)

    def end(self):
        """
        Enf of connection : we need to close sthe qlite connection
        """
        if self.initialized:
            self._db.close()
            del self._db
            QSqlDatabase.removeDatabase('')
        super(Storage, self).end()

    def db_error(self, error, prefix=None):
        """
        Compose a string error from a sql error and a prefix
        """
        if not error or not error.isValid():
            return prefix or ''

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
                    str_e = self.db_error(query.lastError(), str_e)
                except:
                    pass
                raise DBUpgradeCannotBeDone(str_e)

            # check fields to update/add/remove
            try:
                query = queries.query('pragma table_info(%s)' % table_name)
                db_fields = {}
                while query.next():
                    name  = str(query.value(1).toString())
                    ftype = str(query.value(2).toString())
                    null  = not query.value(3).toBool()
                    if query.value(4).isNull:
                        default = None
                    else:
                        default = str(query.value(4).toString())
                    db_fields[name] = (name, ftype, null, default)

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
                        log_str = 'Table "%s" is going to be updated :' % table_name
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
                        for field in fields:
                            query = queries.query(queries.alter_table_add_field_query(table, field))
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
                    str_e = self.db_error(query.lastError(), str_e)
                except:
                    pass
                raise DBUpgradeCannotBeDone(str_e)

    def prepare_queries(self):
        for table_name, table in queries.TABLES.iteritems():
            self._prepared_queries[table_name] = {}

            # read one entry
            read_object = QSqlQuery()
            read_object.prepare(
                queries.select_query(
                    table  = table,
                    where  = 'id=:id',
                )
            )
            self._prepared_queries[table_name]['read_object'] = read_object

            # add one entry
            add_object = QSqlQuery()
            add_object.prepare(
                queries.insert_query(
                    table  = table,
                )
            )
            self._prepared_queries[table_name]['add_object'] = add_object

            # delete one entry
            delete_object = QSqlQuery()
            delete_object.prepare(
                queries.delete_query(
                    table  = table,
                    where  = 'id=:id',
                )
            )
            self._prepared_queries[table_name]['delete_object'] = delete_object

    def query_row_to_dict(self, query, table):
        """
        Convert a record from a sqlresult and return a dict. Use fields provided in the table parameter
        """
        data = {}
        for i in range(len(table['ordered_fields'])):
            field_name = table['ordered_fields'][i]
            ftype = table['fields'][field_name][1]

            if query.isNull(i):
                value = None
            else:
                value = query.value(i)
                if 'INT' in ftype:
                    value = value.toInt()[0]
                else:
                    value = str(value.toString())
            data[field_name] = value

        return data

    def add_object(self, object_type, data):
        """
        Add an object of a certain type, with some data (a dict)
        Return the pk of the new entry
        Raise CannotAddObject if it fails
        """
        self.assert_ready()
        table = queries.TABLES[object_type]

        query = QSqlQuery(self._prepared_queries[object_type]['add_object'])
        for field in table['ordered_fields']:
            query.bindValue(':%s' % field, data.get(field, QVariant(None)))

        if not query.exec_():
            lastDBError = self._db.lastError()
            if lastDBError.type():
                raise StorageTemporarilyNotAvailable(lastDBError.text())
            raise CannotAddObject(self.db_error(query.lastError(), 'Object of type "%s" cannot be added' % object_type))

        # if the table has an autoincrement primary key, return the new pk
        if table.get('pk', {}).get('autoincrement', False):
            if not table['pk']['field'] in data:
                return query.lastInsertId().toInt()[0]

        # else return the pk from the data
        if 'pk' in table and table['pk']['field'] in data:
            return data[table['pk']['field']]

        # else, no pk, return None
        return None

    def read_object(self, object_type, id):
        """
        Read the object of a certain type with the specified id
        Return a dict
        Raise CannotReadObject if it fails and ObjectNotFound if not found
        """
        self.assert_ready()
        table = queries.TABLES[object_type]

        query = QSqlQuery(self._prepared_queries[object_type]['read_object'])
        query.setForwardOnly(True)
        query.bindValue(':id', id)

        if not query.exec_():
            lastDBError = self._db.lastError()
            if lastDBError.type():
                raise StorageTemporarilyNotAvailable(lastDBError.text())
            raise CannotReadObject(self.db_error(query.lastError(), 'Object "%s" of type "%s" cannot be read' % (id, object_type)))

        if not query.next():
            raise ObjectNotFound('Object "%s" of type "%s" cannot be found' % (id, object_type))

        return self.query_row_to_dict(query, table)

    def update_object(self, object_type, id, data):
        """
        Update the object of a certain type with the specified id, with the given data (a dict field=>value)
        Raise CannotUpdateObject if it fails and ObjectNotFound if not found
        """
        self.assert_ready()
        table = queries.TABLES[object_type]

        fields = data.keys()
        query = QSqlQuery()
        query.prepare(queries.update_query(
            table  = table,
            fields = fields,
            where  = 'id=:id',
        ))
        query.bindValue(':id', id)
        for field, value in data.iteritems():
            query.bindValue(':%s' % field, value)

        if not query.exec_():
            lastDBError = self._db.lastError()
            if lastDBError.type():
                raise StorageTemporarilyNotAvailable(lastDBError.text())
            raise CannotUpdateObject(self.db_error(query.lastError(), 'Object "%s" of type "%s" cannot be updated' % (id, object_type)))

        if not query.numRowsAffected():
            raise ObjectNotFound('Object "%s" of type "%s" cannot be found' % (id, object_type))

    def delete_object(self, object_type, id):
        """
        Delete the object of a certain type with the specified id
        Raise CannotDeleteObject if it fails and ObjectNotFound if not object is not found
        """
        self.assert_ready()
        table = queries.TABLES[object_type]

        query = QSqlQuery(self._prepared_queries[object_type]['delete_object'])
        query.bindValue(':id', id)

        if not query.exec_():
            lastDBError = self._db.lastError()
            if lastDBError.type():
                raise StorageTemporarilyNotAvailable(lastDBError.text())
            raise CannotDeleteObject(self.db_error(query.lastError(), 'Object "%s" of type "%s" cannot be deleted' % (id, object_type)))

        if not query.numRowsAffected():
            raise ObjectNotFound('Object "%s" of type "%s" cannot be found' % (id, object_type))
