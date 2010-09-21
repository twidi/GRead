# -*- coding: utf-8 -*-

def default_view_mode():
    return 'maemo5'

view_mode = default_view_mode()
_controller_module = __import__('.'.join(['views', view_mode, 'controller']), globals(), locals(), ['Controller'])
Controller = getattr(_controller_module, 'Controller')
