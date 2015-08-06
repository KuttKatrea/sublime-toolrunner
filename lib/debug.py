import sys
import datetime

enabled = True

def log(*args):
    if enabled:
        print(*([ "[ToolRunner][%s]" % datetime.datetime.now().strftime('%H:%M:%S.%f') ] + list(args)))

def forget_modules():
    log("Deleting submodules")
    deletekeys = []
    for key in sys.modules:
        if key.startswith(__package__):
            deletekeys.append(key)

    for key in deletekeys:
        del sys.modules[key]
