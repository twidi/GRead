# -*- coding: utf-8 -*-

"""
Settings view
"""
from PyQt4.QtGui import *
from PyQt4.QtCore import *
    
from ui.Ui_settings import Ui_Settings
from engine.signals import SIGNALS
from engine import settings

class SettingsDialog(object):
    def __init__(self, controller):
        self.controller = controller
        self.created = False
        self.google_was_verified = False
        self.google_credentials_changed = False

    def get_ui_class(self):
        return Ui_Settings
        
    def create(self):
        self.dialog = QDialog()
        self.ui = self.get_ui_class()()
        self.ui.setupUi(self.dialog)
        self.dialog.setWindowTitle("%s - Settings" % QApplication.applicationName())
        self.created = True
        
    def open(self):
        # create dialog
        if not self.created:
            self.create()
        self.update_inputs()
        self.dialog.exec_()
        self.read_inputs()
        self.save_settings()
        
    def update_inputs(self):
        self.ui.inputSettingsAccount.setText( settings.get('google', 'account'))
        self.ui.inputSettingsPassword.setText(settings.get('google', 'password'))
        try:
            self.ui.selectSettingsHomeDefault.setCurrentIndex(settings.helpers['feeds_default'].index(settings.get('feeds', 'default')))
        except:
            self.ui.selectSettingsHomeDefault.setCurrentIndex(0)
    
        self.ui.checkSettingsHomeShowUnread.setChecked(settings.get('feeds', 'unread_only'))
    
        self.ui.checkSettingsShowShared.setChecked(    settings.get('feeds', 'show_broadcast'))
        self.ui.checkSettingsShowStarred.setChecked(   settings.get('feeds', 'show_starred'))
        self.ui.checkSettingsShowNotes.setChecked(     settings.get('feeds', 'show_created'))
        self.ui.checkSettingsShowAll.setChecked(       settings.get('feeds', 'show_reading-list'))
        self.ui.checkSettingsShowRead.setChecked(      settings.get('feeds', 'show_read'))
        self.ui.checkSettingsShowFriends.setChecked(   settings.get('feeds', 'show_broadcast-friends'))
    
        try:
            self.ui.selectSettingsItemsShowMode.setCurrentIndex(settings.helpers['items_show_mode'].index(settings.get('items', 'show_mode')))
        except:
            self.ui.selectSettingsItemsShowMode.setCurrentIndex(0)
            
    def read_inputs(self):
        self.google_credentials_changed = False
        self.google_was_verified        = settings.get('google', 'verified')
        
        google_account  = self.ui.inputSettingsAccount.text()
        google_password = self.ui.inputSettingsPassword.text()

        if settings.get('google', 'account') != google_account \
        or settings.get('google', 'password') != google_password:
            settings.set('google', 'verified', False)
            settings.set('google', 'auth_token', '')
            settings.set('google', 'token', '')
            self.google_credentials_changed = True
        settings.set('google', 'account', google_account)
        settings.set('google', 'password', google_password)
    
        try:
            settings.set('feeds', 'default', settings.helpers['feeds_default'][self.ui.selectSettingsHomeDefault.currentIndex()])
        except:
            pass
    
        settings.set('feeds', 'unread_only', self.ui.checkSettingsHomeShowUnread.isChecked())
    
        settings.set('feeds', 'show_broadcast',         self.ui.checkSettingsShowShared.isChecked())
        settings.set('feeds', 'show_starred',           self.ui.checkSettingsShowStarred.isChecked())
        settings.set('feeds', 'show_created',           self.ui.checkSettingsShowNotes.isChecked())
        settings.set('feeds', 'show_reading-list',      self.ui.checkSettingsShowAll.isChecked())
        settings.set('feeds', 'show_read',              self.ui.checkSettingsShowRead.isChecked())
        settings.set('feeds', 'show_broadcast-friends', self.ui.checkSettingsShowFriends.isChecked())
        # old stuff
        settings.set('feeds', 'show_kept-unread',       False)
    
        try:
            settings.set('items', 'show_mode', settings.helpers['items_show_mode'][self.ui.selectSettingsItemsShowMode.currentIndex()])
        except:
            pass
    
    def save_settings(self):
        settings.save()
        self.controller.emit(SIGNALS['settings_updated'], not self.google_was_verified and self.google_credentials_changed)
