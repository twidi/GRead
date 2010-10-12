# -*- coding: utf-8 -*-

from os import environ

def detect_view_mode():
    view_mode = None
    
    # detect if maemo5
    try:
        from PyQt4 import QtMaemo5
    except:
        pass
    else:
        view_mode = 'maemo5'
        
    # detect if maemo4
    if not view_mode and "OS 2008" in environ.values():
        view_mode = 'maemo4'
        
    # default = basic
    if not view_mode:
        view_mode = 'basic'
        
    # return detected view mode
    return view_mode

# detect default view mode
view_mode = 'maemo4'#detect_view_mode()

# provide direct access to correct controller class
_controller_module = __import__('.'.join(['views', view_mode, 'controller']), globals(), locals(), ['Controller'])
Controller = getattr(_controller_module, 'Controller')
