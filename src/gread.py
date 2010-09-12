#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt4.QtGui import QApplication

# currently only one view mode : maemo5
from views.maemo5.controller import Controller
from engine import settings

import sys
sys.setdefaultencoding("utf-8")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    settings.load()
    controller = Controller()
    controller.run()
    result = app.exec_()
    sys.exit(result)


