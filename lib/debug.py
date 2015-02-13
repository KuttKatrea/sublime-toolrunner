enabled = True

def log(*args, **kwargs):
    if enabled:
        print(*(["[ToolRunner]"] + list(args)))
