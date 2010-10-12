# -*- coding: utf-8 -*-

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from ..mobile import ViewEventFilter as MobileViewEventFilter,  \
                     View            as MobileView
                    
from engine import settings

class ViewEventFilter(MobileViewEventFilter):
    pass
    
class View(MobileView):
    pass

from .. import basic
basic.base_view_class = View
basic.base_eventfilter_class = ViewEventFilter
