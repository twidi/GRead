Step to create deb package :


1. Install py2deb:

# apt-get install python2.5-py2deb

2. Correct a bug in py2deb by editing /usr/lib/python2.5/site-packages/py2deb.py line 382 changing it from: 


	bugtrackerstr = "XSBC-Bugtracker: %s" % ( self.xsbc_bugtracker )

to

	bugtrackerstr = self.xsbc_bugtracker

3. Build the package

$ run-standalone.sh python2.5 ./build_gread.py

4. Manage .so file..

You must comment or remove the 'dh_strip' in the .py2deb_build_folder/debian/rules file

And then call 

$ python rebuild_after_deb2py_and_removing_dh_strip.py

And finally move gread from .pydeb_build_folder to fremantle one

Yes, it's ugly. I know.
