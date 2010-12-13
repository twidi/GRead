# -*- coding: utf-8 -*-

import os
from engine import settings, log
from views import view_mode

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






