Step to create deb package :


1. Install py2deb:

# apt-get install python2.5-py2deb

2. Correct a bug in py2deb by editing /usr/lib/python2.5/site-packages/py2deb.py line 382 changing it from: 


	bugtrackerstr = "XSBC-Bugtracker: %s" % ( self.xsbc_bugtracker )

to

	bugtrackerstr = self.xsbc_bugtracker

3. Prepare build

	a) copy src directory to packaging/fremantle/src/opt/GRead if needed (updates in GRead code)

	b) Update infomations (version, build and changelog) in build_gread_step1.py and build_gread_step2.py (in the future it should be one in only one place)

4. Build the package

$ run-standalone.sh python2.5 ./build_gread_step1.py

5. Update debian rules

You must comment or remove the 'dh_strip and dh_shlibdeps' in the .py2deb_build_folder/gread/debian/rules file

6. Add a pretty name

Add the following line in the .py2deb_build_folder/gread/debian/control file : 

	XSBC-Maemo-Display-Name: GRead

7. Finalize

$ run-standalone.sh python2.5 ./build_gread_step2.py

And finally move gread_* files from .pydeb_build_folder to fremantle one

8. The end

Yes, maybe it's ugly. I know. Please help me to do it in a better way.
