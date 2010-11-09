import sys

DEBUG = '--debug' in sys.argv

if DEBUG :
    import time
    def log(string):
        sys.stderr.write("%s - %s\n" % (time.time(), string))
else:
    def log(string):
        pass
