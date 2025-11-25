import inspect


# Given a module, get the names of all classes defined within the module
def getClasses(module):
    classes = []
    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and obj.__module__ == module.__name__:
            classes.append(obj)
    return classes