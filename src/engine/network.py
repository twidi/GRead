# -*- coding: utf-8 -*-

"""
A module with utilities to wait for network
TODO: ask for network on maemo
"""

import urllib2, socket, time
socket.setdefaulttimeout(10)

test_request = urllib2.Request('https://www.google.com/reader/api/0/user-info')
available = True

def wait():
    """
    Wait until network is available
    """
    global available
    available = False
    while True:
        if ping():
            break
        time.sleep(10)

def ping():
    """
    Ping an url to test if network is available.
    Return True (if network is available) or False
    """
    global test_request, available
    try:
        response = urllib2.urlopen(test_request)
    except urllib2.HTTPError:
        available = True
    except urllib2.URLError, e:
        # no network...
        pass
    else:
        response.close()
        available = True
    return available
