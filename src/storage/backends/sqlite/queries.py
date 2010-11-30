# -*- coding: utf-8 -*-

from PyQt4.QtSql import *
from engine import DEBUG, log
import copy

TABLES = {
    'account': {
        'fields': {
            'id':       ('INTEGER',      False, None),
            'login':    ('VARCHAR(50)',  True,  None),
            'password': ('VARCHAR(255)', True,  None),
            'token1':   ('TEXT',         True,  None),
            'token2':   ('TEXT',         True,  None),
        },
        'pk': {
            'field':         'id',
            'autoincrement': True,
        },
    },
}

# add name in each table dict, and field name at first position of each field tuple
for table_name, table in TABLES.iteritems():
    table['name'] = table_name
    for field_name in table['fields']:
        table['fields'][field_name] = (field_name,) + table['fields'][field_name]
    table['ordered_fields'] = table['fields'].keys()


CREATE_TABLE = "CREATE TABLE IF NOT EXISTS %(table_name)s (%(fields)s %(pk)s)"

CREATE_TABLE_FIELD_PART = "%(name)s %(type)s %(null)s %(default)s"

CREATE_TABLE_PK_PART = "PRIMARY KEY (%(pk)s)"

ALTER_TABLE = "ALTER TABLE %(table_name)s %(alter)s"

ALTER_TABLE_ADD_COLUMN_PART = "ADD %(field)s"

ALTER_TABLE_RENAME_TABLE_PART = "RENAME TO %(new_table_name)s"

INSERT = "INSERT INTO %(table_name)s %(values)s"

INSERT_VALUES_PART = "(%(fields)s) VALUES (%(values)s)"

SELECT = "SELECT %(fields)s FROM %(table_name)s %(where)s %(order)s %(limit)s"

WHERE_PART = "WHERE %(filters)s"

SELECT_ORDER_PART = "ORDER BY %(fields)s"

SELECT_ORDER_FIELD_PART = "%(field)s %(sort)s"

SELECT_LIMIT_PART = "LIMIT %(limit)s, %(offset)s"

DROP_TABLE = "DROP TABLE %(table_name)s"

UPDATE = "UPDATE %(table_name)s SET %(sets)s %(where)s"

UPDATE_SET_PART = "%(field)s = %(value)s"

DELETE = "DELETE FROM %(table_name)s %(where)s"

def query(query, debug=None):
    if debug is None:
        debug = DEBUG
    if debug:
        log(query)
    return QSqlQuery(query)

def create_field_query(field):
    name, ftype, null, default = field
    null = 'NULL' if null else 'NOT NULL'
    default = default if default is not None else ''
    return CREATE_TABLE_FIELD_PART % {
        'name':    name,
        'type':    ftype,
        'null':    null,
        'default': default,
    }

def create_table_query(table):
    table_fields = table['fields']

    pk = ''
    if 'pk' in table:
        if table['pk'].get('autoincrement', False):
            table_fields = copy.copy(table_fields)
            field_tuple = table_fields[table['pk']['field']]
            field_tuple = (
                field_tuple[0],
                field_tuple[1] + ' PRIMARY KEY',
                field_tuple[2],
                field_tuple[3],
            )
            table_fields[table['pk']['field']] = field_tuple
        else:
            pk = CREATE_TABLE_PK_PART % {
                'pk': ', %s' % table['pk']['field'],
            }

    fields = []
    for field_name, field in table_fields.iteritems():
        fields.append(create_field_query(field))

    return CREATE_TABLE % {
        'table_name': table['name'],
        'fields':     ', '.join(fields),
        'pk':         pk,
    }
    
def alter_table_add_fields_query(table, fields):
    alter = ', '.join(
        [
            ALTER_TABLE_ADD_COLUMN_PART % {
                'field': create_field_query(field),
            } for field in fields
        ]
    )
    return ALTER_TABLE % {
        'table_name': table['name'],
        'alter':      alter,
    }

def rename_table_query(table, new_table_name):
    alter = ALTER_TABLE_RENAME_TABLE_PART % {
        'new_table_name': new_table_name,
    }
    return ALTER_TABLE % {
        'table_name': table['name'],
        'alter': alter,
    }


def where_part(where):
    if where:
        return WHERE_PART % {
            'filters': where
        }
    else:
        return ''

def select_query(table, fields=None, where=None, order=None, limit=None, offset=None):

    # fields
    if fields is None:
        fields = table['ordered_fields']

    # where
    where = where_part(where)

    # order by
    if order:
        if type(order) == dict:
            order = (order,)
        orders = []
        for o in order:
            sort  = ''
            if o not in (list, tuple):
                field = o
            else:
                field = o[0]
                if o[1] in ('ASC', 'DESC',):
                    sort ='ASC' if o[1] else 'DESC'
            orders.append(
                SELECT_ORDER_FIELD_PART % {
                    'field': o[0],
                    'sort':  sort,
                }
            )
        order = SELECT_ORDER_PART % {
            'fields': order
        }
    else:
        order = ''

    # limit
    if limit:
        if not offset:
            offset = 0
        limit = SELECT_LIMIT_PART % {
            'limit': limit,
            'offset': offset,
        }
    else:
        limit = ''

    # final query
    return SELECT % {
        'table_name': table['name'],
        'fields': ', '.join(fields),
        'where': where,
        'order': order,
        'limit': limit,
    }

def insert_into_select_query(src_table, dest_table, fields):
    select = select_query(src_table, fields)
    return INSERT % {
        'values': select,
        'table_name': dest_table['name'],
    }

def insert_query(table, fields=None):
    if not fields:
        fields = table['ordered_fields']
    values = INSERT_VALUES_PART % {
        'fields': ', '.join(fields),
        'values': ', '.join([":%s" % field for field in fields]),
    }
    return INSERT % {
        'table_name': table['name'],
        'values':     values
    }

def drop_table_query(table):
    return DROP_TABLE % {
        'table_name': table['name'],
    }

def update_query(table, fields=None, where=None):

    # fields
    if fields is None:
        fields = table['ordered_fields']

    # where
    where = where_part(where)

    # sets
    sets = [
        UPDATE_SET_PART % {
            'field': field,
            'value': ":%s" % field,
        }
        for field in fields
    ]

    # final query
    return UPDATE % {
        'table_name': table['name'],
        'sets':       ', '.join(sets),
        'where':      where,
    }

def delete_query(table, where=None):

    # where
    where = where_part(where)
    
    # final query
    return DELETE % {
        'table_name': table['name'],
        'where':      where,
    }
