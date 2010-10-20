Step to create deb package :


1. Install py2deb:

# apt-get install python2.5-py2deb

2. Correct a bug in py2deb by editing /usr/lib/python2.5/site-packages/py2deb.py line 382 changing it from: 


	bugtrackerstr = "XSBC-Bugtracker: %s" % ( self.xsbc_bugtracker )

to

	bugtrackerstr = self.xsbc_bugtracker

3. Build the package

$ run-standalone.sh python2.5 ./build_gread_step1.py

4. Manage .so file..

You must comment or remove the 'dh_strip' in the .py2deb_build_folder/gread/debian/rules file

5. Add some build-depends

On the line "Build-Depends" in .py2deb_build_folder/gread/debian/control file add

, libqt4-gui (>=4.6), libqt4-dev (>= 4.6), libx11-dev, x11proto-core-dev

6. Finalize

$ run-standalone.sh python2.5 ./build_gread_step2.py

And finally move gread from .pydeb_build_folder to fremantle one

7. The end

Yes, it's ugly. I know. Please help me to do it in a better way.
