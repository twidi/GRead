import sys

DEBUG = '--debug' in sys.argv

if DEBUG :
    def log(string):
        sys.stderr.write("%s\n" % string)
else:
    def log(string):
        pass
