#-*- test-case-name: gyro.test.test_config
"""
Configuration file that lets you set different configurations based on which
machine it is being run on. 
"""
import ast
import json
from twisted.python import filepath
import os.path

class ConfigFile(object):
    """
    A configuration file
    """

    def __init__(self, config_file, ids=None):
        """
        @param configFile: Either a filename or a file like object
        """
        self.ids = ids or []
        self.config = {}

        if isinstance(config_file, basestring):
            with open(config_file, 'r') as f:
                self.load_from_file(f)
        else:
            self.load_from_file(config_file)

    def load_from_file(self, f):
        """
        Load a configuration file
        """
        for line in f.readlines():
            if not line.startswith("#"):
                try:
                    key, value = line.strip().split('=', 1)
                    k, v = key.strip(), value.strip()

                    try:
                        self.config[k] = ast.literal_eval(v)
                    except:
                        if ((v.startswith('"') and v.endswith('"')) or
                            (v.startswith("'") and v.endswith("'"))):
                            self.config[k] = v[1:-1]
                        else:
                            self.config[k] = v
                except ValueError:
                    pass

    def get(self, key, default=None, ids=[]):
        """
        Get a key from our configuration file. We get try and get an id specific
        version of the key/value according to our identifiers, otherwise we
        return the global value if it exists, and finally the default if it
        isn't set
        """
        ids = ids or []
        for id in ids + self.ids:
            v = "%%%s.%s" % (id, key)
            if v in self.config:
                return self.config[v]

        return self.config.get(key, default)

    def __str__(self):
        return "ConfigFile(%s) : ids - %s\n%s" % (self.filename,
                self.ids, self.config)

CONFIG_FILE = None

def get(key, default=None, ids=None):
    """
    Get the value for C{key} if it exists, else return default
    """
    return CONFIG_FILE.get(key, default, ids) if CONFIG_FILE else default

def load(filename, ids=None):
    """
    Load a configuration file
    """
    global CONFIG_FILE
    CONFIG_FILE = ConfigFile(filename, ids or get_ids())

def get_deployment_ids_path():
    """
    Return the path where the deployment_ids.txt file is stored
    """
    return os.path.join(os.path.dirname(__file__), 'deployment_ids.txt')
     
def set_ids(ids):
    """
    Set the identifiers for this machine
    """
    with open(get_deployment_ids_path(), 'w') as f:
        f.write(json.dumps(ids))

def get_ids():
    """
    Get the deployment ID of this machine
    """
    try:
        with open(get_deployment_ids_path(), 'r') as f:
            return json.loads(f.read().strip())
    except:
        return []

def get_project_file(name, default):
    fn = get(name, default)
    global app_path
    return os.path.join(app_path, fn)
