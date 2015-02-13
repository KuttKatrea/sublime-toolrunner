import sys

enabled = True

def log(*args, **kwargs):
    if enabled:
        print(*(["[ToolRunner]"] + list(args)))

def forget_modules():
    log("Deleting submodules")
    deletekeys = []
    for key in sys.modules:
        if key.startswith(__package__):
            deletekeys.append(key)

    for key in deletekeys:
        del sys.modules[key]
