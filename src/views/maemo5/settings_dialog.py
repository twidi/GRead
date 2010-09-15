# -*- coding: utf-8 -*-

"""
Settings view
"""
from PyQt4.QtGui import *
from PyQt4.QtCore import *
    
from views.maemo5.ui.Ui_settings import Ui_Settings
from views.maemo5 import MAEMO5_PRESENT
from engine.signals import SIGNALS
from engine import settings

def show_settings(controller):
    # create dialog
    Settings = QDialog()
    ui = Ui_Settings()
    ui.setupUi(Settings)
    Settings.setWindowTitle("%s - Settings" % QApplication.applicationName())

    # fill inputs
    ui.inputSettingsAccount.setText( settings.get('google', 'account'))
    ui.inputSettingsPassword.setText(settings.get('google', 'password'))
    try:
        ui.selectSettingsHomeDefault.setCurrentIndex(settings.helpers['feeds_default'].index(settings.get('feeds', 'default')))
    except:
        ui.selectSettingsHomeDefault.setCurrentIndex(0)

    ui.checkSettingsHomeShowUnread.setChecked(settings.get('feeds', 'unread_only'))

    ui.checkSettingsShowShared.setChecked(    settings.get('feeds', 'show_broadcast'))
    ui.checkSettingsShowStarred.setChecked(   settings.get('feeds', 'show_starred'))
    ui.checkSettingsShowNotes.setChecked(     settings.get('feeds', 'show_created'))
    ui.checkSettingsShowAll.setChecked(       settings.get('feeds', 'show_reading-list'))
    ui.checkSettingsShowRead.setChecked(      settings.get('feeds', 'show_read'))
    ui.checkSettingsShowFriends.setChecked(   settings.get('feeds', 'show_broadcast-friends'))

    try:
        ui.selectSettingsItemsShowMode.setCurrentIndex(settings.helpers['items_show_mode'].index(settings.get('items', 'show_mode')))
    except:
        ui.selectSettingsItemsShowMode.setCurrentIndex(0)

    if MAEMO5_PRESENT:
        ui.checkSettingsPortraitMode.setChecked(settings.get('other', 'portrait_mode'))
    else:
        ui.checkSettingsPortraitMode.hide()

    ui.checkSettingsScrollTitles.setChecked(settings.get('other', 'scroll_titles'))

    # display window
    Settings.exec_()
    
    # save new settings
    google_credentials_changed = False
    google_was_verified        = settings.get('google', 'verified')
    google_account  = ui.inputSettingsAccount.text()
    google_password = ui.inputSettingsPassword.text()
    if settings.get('google', 'account') != google_account \
    or settings.get('google', 'password') != google_password:
        settings.set('google', 'verified', False)
        settings.set('google', 'auth_token', '')
        settings.set('google', 'token', '')
        google_credentials_changed = True
    settings.set('google', 'account', google_account)
    settings.set('google', 'password', google_password)

    try:
        settings.set('feeds', 'default', settings.helpers['feeds_default'][ui.selectSettingsHomeDefault.currentIndex()])
    except:
        pass

    settings.set('feeds', 'unread_only', ui.checkSettingsHomeShowUnread.isChecked())

    settings.set('feeds', 'show_broadcast',         ui.checkSettingsShowShared.isChecked())
    settings.set('feeds', 'show_starred',           ui.checkSettingsShowStarred.isChecked())
    settings.set('feeds', 'show_created',           ui.checkSettingsShowNotes.isChecked())
    settings.set('feeds', 'show_reading-list',      ui.checkSettingsShowAll.isChecked())
    settings.set('feeds', 'show_read',              ui.checkSettingsShowRead.isChecked())
    settings.set('feeds', 'show_broadcast-friends', ui.checkSettingsShowFriends.isChecked())
    # old stuff
    settings.set('feeds', 'show_kept-unread',       False)

    try:
        settings.set('items', 'show_mode', settings.helpers['items_show_mode'][ui.selectSettingsItemsShowMode.currentIndex()])
    except:
        pass

    if MAEMO5_PRESENT:
        settings.set('other', 'portrait_mode', ui.checkSettingsPortraitMode.isChecked())

    settings.set('other', 'scroll_titles', ui.checkSettingsScrollTitles.isChecked())
        
    settings.save()

    controller.emit(SIGNALS['settings_updated'], not google_was_verified and google_credentials_changed)
            
