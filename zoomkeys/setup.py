from distutils.core import setup, Extension, os

class PkgConfig(object):
    def __init__(self, names):
        def stripfirsttwo(string):
            return string[2:]
        self.libs = map(stripfirsttwo, os.popen("pkg-config --libs-only-l %s" % names).read().split())
        self.libdirs = map(stripfirsttwo, os.popen("pkg-config --libs-only-L %s" % names).read().split())
        self.incdirs = map(stripfirsttwo, os.popen("pkg-config --cflags-only-I %s" % names).read().split())

flags = PkgConfig("QtGui x11")

module1 = Extension('zoomkeys',
    sources = ['zoomkeys.cpp'],
    include_dirs = flags.incdirs + ['.'],  
    libraries = flags.libs,
    library_dirs = flags.libdirs,
    runtime_library_dirs = flags.libdirs
)

setup (name = 'ZoomKeys',
    version = '1.0',
    author = 'S.Angel / Twidi', 
    author_email = 's.angel@twidi.com', 
    description = 'A package for grabing Zoom Keys',
    ext_modules = [module1],
)
