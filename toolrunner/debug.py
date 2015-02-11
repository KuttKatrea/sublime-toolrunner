debug_enabled = True

def log(*args, **kwargs):
    if debug_enabled:
        print(*args)
