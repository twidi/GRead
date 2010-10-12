Step to create deb package :


1. Install py2deb:

# apt-get install python2.5-py2deb

2. Correct a bug in py2deb by editing /usr/lib/python2.5/site-packages/py2deb.py line 382 changing it from: 


	bugtrackerstr = "XSBC-Bugtracker: %s" % ( self.xsbc_bugtracker )

to

	bugtrackerstr = self.xsbc_bugtracker

3. Build the package

$ run-standalone.sh python2.5 ./build_gread.py

