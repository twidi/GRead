# -*- coding: utf-8 -*-

"""
Settings manager.
Usage : 
import settings
settings.load()
value = settings.get('group', 'key')
settings.set('group', 'key', value, save=False)
settings.save()
# utils : settings.special_feeds, settings.auth_ready, settings.legal
"""

from PyQt4.QtCore import QSettings
from PyQt4.QtGui import QApplication
from utils.libgreader import GoogleReader

__ALL__ = ('load', 'save', 'get', 'set', 'auth_ready', 'special_feeds')

# about the application, organization and author
legal = {
    'organization': {
        'name': 'Twidi.com', 
        'domain': 'twidi.com', 
    }, 
    'application': {
        'name': 'Gread', 
    }, 
    'author': {
        'name': 'S.Angel / Twidi', 
        'email': 's.angel@twidi.com', 
    }
}


QApplication.setOrganizationName(legal['organization']['name'])
QApplication.setOrganizationDomain(legal['organization']['domain'])
QApplication.setApplicationName(legal['application']['name'])


# will hold the settings
_settings = {}
# will hold the QString object
_qsettings = None

# helpers for special settings
helpers = {
    'feeds_default': ['feeds', 'labels', ], # list and not tuple for using index method

    'feeds_specials': GoogleReader.SPECIAL_FEEDS,
    
    'items_show_mode': ('all-save', 'unread-save', 'all-nosave', 'unread-nosave'), 

    'booleans': (
        'google.verified',
                 
        'feeds.show_' + GoogleReader.STARRED_LIST, 
        'feeds.show_' + GoogleReader.SHARED_LIST, 
        'feeds.show_' + GoogleReader.READING_LIST, 
        'feeds.show_' + GoogleReader.READ_LIST, 
        'feeds.show_' + GoogleReader.NOTES_LIST, 
        'feeds.show_' + GoogleReader.FRIENDS_LIST, 
        'feeds.show_' + GoogleReader.KEPTUNREAD_LIST, 

        'feeds.unread_only',

        'other.portrait_mode',
        'other.scroll_titles',
    ), 
}

# all available settings and their default values
_default = {
    'google': {
        'account': '',
        'password': '',
        'verified': False,
        'auth_token': '', 
        'token': '', 
    },
    'feeds': {
        'default':     'labels', # feeds or labels
        'unread_only': True,    # display all, or only unread feeds
        'unread_number': '100',   # number of unread items to fetch while synchronizing
        # special lists : 
        'show_' + GoogleReader.STARRED_LIST:   True,
        'show_' + GoogleReader.SHARED_LIST:     False, 
        'show_' + GoogleReader.READING_LIST:    False,
        'show_' + GoogleReader.READ_LIST:       False,
        'show_' + GoogleReader.NOTES_LIST:      False,
        'show_' + GoogleReader.FRIENDS_LIST:    True,
        'show_' + GoogleReader.KEPTUNREAD_LIST: False,
    }, 
    'items': {
        'show_mode': 'unread-save', # all-save, unread-save, all-nosave, unread-nosave
    }, 
    'other': {
        'portrait_mode': False,
        'scroll_titles': True,
    }
}

# list of all special feeds with their name
special_feeds = {
    GoogleReader.STARRED_LIST:    { 'name': 'Starred',}, 
    GoogleReader.SHARED_LIST:     { 'name': 'Shared',}, 
    GoogleReader.READING_LIST:    { 'name': 'All',}, 
    GoogleReader.READ_LIST:       { 'name': 'Read',}, 
    GoogleReader.NOTES_LIST:      { 'name': 'Notes',}, 
    GoogleReader.FRIENDS_LIST:    { 'name': 'Friends',}, 
    GoogleReader.KEPTUNREAD_LIST: { 'name': 'Kept unread',}, 
}

def load():
    """
    Load settings from file or whatever via QSettings
    """
    global _qsettings, _settings, _default, helpers
    if not _qsettings:
        _qsettings = QSettings()
    new_settings = {}
    for group in _default:
        _qsettings.beginGroup(group)
        new_settings[group] = {}
        for key in _default[group]:
            value = _qsettings.value(key, _default[group][key])
            if '%s.%s' % (group, key) in helpers['booleans']:
                new_settings[group][key] = value.toBool()
            else:
                new_settings[group][key] = value.toString()
        _qsettings.endGroup()
    _settings = new_settings

def save():
    """
    Save settings into file or whatever via QSettings
    """
    global _qsettings, _settings
    for group in _settings:
        _qsettings.beginGroup(group)
        for key in _settings[group]:
             _qsettings.setValue(key, _settings[group][key])
        _qsettings.endGroup()
        
def get(group, key):
    """
    Return a value for the specified settings, or None
    """
    global _default, _settings
    return _settings.get(group, {}).get(key, _default.get(group, {}).get(key, None))

def set(group, key, value, save_all=False):
    """
    Set the specified value for a settings, and save all settings if 
    save_all is True
    """
    global _settings
    _settings.setdefault(group, {})[key] = value
    if save_all:
        save()
        
def auth_ready():
    """
    Return True if either google account and password are filled
    """
    global _settings
    return (_settings['google']['account'].replace(' ', '') != '' and _settings['google']['password'].replace(' ', '') != '')
