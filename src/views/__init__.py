# -*- coding: utf-8 -*-

def detect_view_mode():
    view_mode = None
    
    # detect if maemo5
    try:
        from PyQt4 import QtMaemo5
    except:
        pass
    else:
        view_mode = 'maemo5'
        
    # default = basic
    if not view_mode:
        view_mode = 'basic'
        
    # return detected view mode
    return view_mode

# detect default view mode
view_mode = detect_view_mode()

# provide direct access to correct controller class
_controller_module = __import__('.'.join(['views', view_mode, 'controller']), globals(), locals(), ['Controller'])
Controller = getattr(_controller_module, 'Controller')

# and same for views
views_module = __import__('.'.join(['views', view_mode]), globals(), locals())
