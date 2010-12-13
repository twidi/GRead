# -*- coding: utf-8 -*-

from PyQt4.QtCore import SIGNAL

# list of all signals (with their signatures) used by the storage thread
SIGNALS = {
    # signals for operation management
    'operation_added':   SIGNAL('operation_added(int)'),
    'operation_started': SIGNAL('operation_started(int)'),
    'operation_ended':   SIGNAL('operation_ended(int)'),

    # signals for actions management
    'add_object_started':    SIGNAL('add_object_started(int)'),
    'add_object_done':       SIGNAL('add_object_done(int)'),
    'read_object_started':   SIGNAL('read_object_started(int)'),
    'read_object_done':      SIGNAL('read_object_done(int)'),
    'update_object_started': SIGNAL('update_object_started(int)'),
    'update_object_done':    SIGNAL('update_object_done(int)'),
    'delete_object_started': SIGNAL('delete_object_started(int)'),
    'delete_object_done':    SIGNAL('delete_object_done(int)'),

    'add_objects_started':    SIGNAL('add_objects_started(int)'),
    'add_objects_done':       SIGNAL('add_objects_done(int)'),
    'read_objects_started':   SIGNAL('read_objects_started(int)'),
    'read_objects_done':      SIGNAL('read_objects_done(int)'),
    'update_objects_started': SIGNAL('update_objects_started(int)'),
    'update_objects_done':    SIGNAL('update_objects_done(int)'),
    'delete_objects_started': SIGNAL('delete_objects_started(int)'),
    'delete_objects_done':    SIGNAL('delete_objects_done(int)'),

    'find_objects_started':            SIGNAL('find_objects_started(int)'),
    'find_objects_done':               SIGNAL('find_objects_done(int)'),
    'find_and_update_objects_started': SIGNAL('find_and_update_objects_started(int)'),
    'find_and_update_objects_done':    SIGNAL('find_and_update_objects_done(int)'),
    'find_and_delete_objects_started': SIGNAL('find_and_delete_objects_started(int)'),
    'find_and_delete_objects_done':    SIGNAL('find_and_delete_objects_done(int)'),
}

