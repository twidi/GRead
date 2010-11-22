import os, time

name = "gread"
description="A Google Reader client with offline capabilities. Can work Offline (synchronize at startup). Works on all platforms where PyQt is available."
author="Stephane Angel aka Twidi"
mail="s.angel@twidi.com"

version = '1.0.7'
buildversion = 1
changelog = "simple gestures in item list on mobile views : swipe to right to mark item as read, and to left to mark item as unread" 

depends = "python2.5, python2.5-qt4-common, python2.5-qt4-gui, python2.5-qt4-webkit, python-simplejson"
 
distribution="fremantle"
arch="all"                #should be all for python, any for all arch
section="user/network"
repository="extras-devel"
urgency="low"             #not used in maemo onl for deb os

TEMP = ".py2deb_build_folder"
DEST = os.path.join(TEMP, name)

# tar
import py2tar
tarcontent= py2tar.py2tar("%(DEST)s" % locals() )
open("%(TEMP)s/%(name)s_%(version)s-%(buildversion)s.tar.gz"%locals(),"wb").write(tarcontent.packed())

# dsc
import py2dsc
import locale
import commands
from subprocess import *
try:
  old_locale,iso=locale.getlocale(locale.LC_TIME)
  locale.setlocale(locale.LC_TIME,'en_US')
except:
  pass
dsccontent = py2dsc.py2dsc("%(version)s-%(buildversion)s"%locals(),
           "%(depends)s"%locals(),
           ("%(TEMP)s/%(name)s_%(version)s-%(buildversion)s.tar.gz"%locals(),),
           Format='1.0',
           Source="%(name)s"%locals(),
           Version="%(version)s-%(buildversion)s"%locals(),
           Maintainer="%(author)s <%(mail)s>"%locals(),                             
           Architecture="%(arch)s"%locals(),
          )

try:
  locale.setlocale(locale.LC_TIME,old_locale)
except:
  pass
f = open("%(TEMP)s/%(name)s_%(version)s-%(buildversion)s.dsc"%locals(),"wb")
f.write(dsccontent._getContent())
f.close()

# changes
import py2changes
try:
  import locale
  old_locale,iso=locale.getlocale(locale.LC_TIME)
  locale.setlocale(locale.LC_TIME,'en_US')
except:
  pass
changescontent = py2changes.py2changes(
                "%(author)s <%(mail)s>"%locals(),
                "%(description)s"%locals(),
                "%(changelog)s"%locals(),
                (
                       "%(TEMP)s/%(name)s_%(version)s-%(buildversion)s.tar.gz"%locals(),
                       "%(TEMP)s/%(name)s_%(version)s-%(buildversion)s.dsc"%locals(),
                ),
                "%(section)s"%locals(),
                "%(repository)s"%locals(),
                Format='1.7',
                Date=time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime()),
                Source="%(name)s"%locals(),
                Architecture="%(arch)s"%locals(),
                Version="%(version)s-%(buildversion)s"%locals(),
                Distribution="%(distribution)s"%locals(),
                Urgency="%(urgency)s"%locals(),
                Maintainer="%(author)s <%(mail)s>"%locals()                             
                )
f = open("%(TEMP)s/%(name)s_%(version)s-%(buildversion)s.changes"%locals(),"wb")
f.write(changescontent.getContent())
f.close()
