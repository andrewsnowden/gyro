"""
Utility functions for Gyro
"""
import os
import sys
from twisted.python.filepath import FilePath
from uuid import uuid1

def uuid():
    return uuid1().hex

def import_class(string, level=-1):
    """
    Import a class based on a string giving module.Class
    """
    module, cls = string.rsplit(".", 1)
    __import__(module, level=level)
    m = sys.modules.get(module)
    c = getattr(m, cls)
    return c

def touch(fname, times = None):
    with file(fname, 'a'):
        os.utime(fname, times)

def create_new_project(name, path=None):
    """
    Create a new gyro project
    """
    
    #TODO redo this

    if not path:
        path = os.getcwd()

    d = FilePath(path).child(name)

    print "Creating new project at '%s'" % (d.path, )

    #Top level directory
    os.mkdir(d.path)

    package = d.child(name.lower())
    os.mkdir(package.path)
    touch(package.child("__init__.py").path, None)

    #Templates
    templates = d.child("templates")
    os.mkdir(templates.path)

    #Public folders
    public = d.child("public")
    os.mkdir(public.path)
    os.mkdir(public.child("js").path)
    os.mkdir(public.child("css").path)
    os.mkdir(public.child("images").path)

    data = FilePath(__file__).sibling("data")

    defaultParams = {
            "name" : name
            }

    #Default configuration
    with open(data.child("app.conf").path) as f:
        conf = f.read()
        with open(d.child("app.conf").path, 'w') as out:
            out.write(conf % defaultParams)

    #Default page
    with open(data.child("app.py").path) as f:
        conf = f.read()
        with open(package.child("app.py").path, 'w') as out:
            out.write(conf % defaultParams)

    #Default template
    with open(data.child("index.html").path) as f:
        conf = f.read()
        with open(templates.child("index.html").path, 'w') as out:
            out.write(conf % defaultParams)

    print "Finished creating project"
