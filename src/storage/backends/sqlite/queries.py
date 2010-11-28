
from PyQt4.QtSql import *
from engine import DEBUG, log
import copy

TABLES = {
	'account': {
		'fields': {
			'id':     ('INTEGER',     False, None),
			'login':  ('VARCHAR(50)', False, None),
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


CREATE_TABLE = "CREATE TABLE IF NOT EXISTS %(table_name)s (%(fields)s %(pk)s)"

CREATE_TABLE_FIELD_PART = "%(name)s %(type)s %(null)s %(default)s"

CREATE_TABLE_PK_PART = "PRIMARY KEY (%(pk)s)"

ALTER_TABLE = "ALTER TABLE %(table_name)s %(alter)s"

ALTER_TABLE_ADD_COLUMN_PART = "ADD %(field)s"

ALTER_TABLE_RENAME_TABLE_PART = "RENAME TO %(new_table_name)s"

INSERT = "INSERT INTO %(table_name)s %(values)s"

SELECT = "SELECT %(fields)s FROM %(table_name)s %(where)s"

DROP_TABLE = "DROP TABLE %(table_name)s"

def query(query, debug=None):
	if debug is None:
		debug = DEBUG
	if debug:
		log(query)
	return QSqlQuery(query)

def create_field_query(field):
	name, type, null, default = field
	null = 'NULL' if null else 'NOT NULL'
	default = default if default is not None else ''
	return CREATE_TABLE_FIELD_PART % {
		'name':    name,
		'type':    type,
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

def insert_into_select_query(src_table, dest_table, fields):
	select = SELECT % {
		'table_name': src_table['name'],
		'fields': ', '.join(fields),
		'where': '',
	}
	return INSERT % {
		'values': select,
		'table_name': dest_table['name'],
	}

def drop_table_query(table):
	return DROP_TABLE % {
		'table_name': table['name'],
	}
