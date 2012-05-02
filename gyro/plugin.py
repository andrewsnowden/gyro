#-*- test-case-name: gyro.test.test_plugin
"""
A plugin infrastructure

Principle taken from:
    http://martyalchin.com/2008/jan/10/simple-plugin-framework/
"""
from gyro import log, config, util, core
import uuid
import os.path

class Error(Exception):
    pass

class PluginNotFoundError(Error):
    pass

def return_or_call(result, fn, *args, **kwargs):
    """
    Return result or the result of the given function
    """
    return result or fn(*args, **kwargs)

class PluginMount(type):
    """
    A metaclass that collects information about plugins
    """
    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, '_plugins'):
            cls._plugins = set()
            cls._plugin_instances = {}
            cls._hooks = {}
        else:
            cls._plugins.add(cls)

        type.__init__(cls, name, bases, attrs)

    def get_plugins(cls):
        """
        All of the available plugin types
        """
        return cls._plugins

    def get_active_plugins(cls):
        """
        Return all of the plugins that are currently active
        """
        return cls._plugin_instances.keys()
        
    def find_plugin_instance(cls, name):
        """
        Find the instance of a plugin with the specified name
        """
        for p in cls.get_active_plugins():
            if p.plugin_name().endswith(name):
                return p

    def find_plugin_by_name(cls, name):
        """
        Find a plugin that matches this name. Although the name can just be the
        class name, you can specify as much of the end part of the module it is
        defined in to ensure that you find the correct plugin
        """
        for p in cls.get_plugins():
            if p.plugin_name().endswith(name):
                return p

        raise PluginNotFoundError("The plugin named '%s' was not found" % (name,
            ))

    def enable_plugin(cls, name, *args, **kwargs):
        """
        Enable a plugin by name string
        """
        p = cls.find_plugin_by_name(name)
        cls._plugin_instances[p] = p(*args, **kwargs)
        cls.add_hooks(p)

    def disable_plugin(cls, name):
        """
        Disable a plugin by name string
        """
        p = cls.find_plugin_by_name(name)
        if p in cls._plugin_instances:
            del cls._plugin_instances[p]
            cls.remove_hooks(p)
            
    def clear(cls):
        """
        Clear all plugins that have been loaded
        """
        cls._plugin_instances = {}
        cls._hooks = {}
        
    def add_hook(cls, name, fn, priority=50):
        """
        Add an arbitrary function as a hook
        """
        class TemporaryPlugin(Plugin):
            priority = 50
            
        setattr(TemporaryPlugin, name, fn)
        cls._plugin_instances[TemporaryPlugin] = TemporaryPlugin()
        cls.add_hooks(TemporaryPlugin)
        return TemporaryPlugin
    
    def add_hooks(cls, p):
        """
        Add all the hooks contained in plugin p
        """
        for attr in dir(p):
            if attr.startswith("on_"):
                if attr in cls._hooks:
                    added = False

                    for i, plug in enumerate(cls._hooks[attr]):
                        if plug.priority > p.priority:
                            cls._hooks[attr].insert(p)
                            added = True
                            break

                    if not added:
                        cls._hooks[attr].append(p)
                else:
                    cls._hooks[attr] = [p]

    def remove_hooks(cls, p):
        """
        Remove all the hooks from plugin p
        """
        for attr in dir(p):
            if attr.startswith("on_"):
                for i, plug in enumerate(cls._hooks[attr]):
                    if plug == p:
                        del cls._hooks[attr][i]
                        break
    
    def run_hook(cls, name, *args, **kwargs):
        """
        Run hook in all plugins containing the specified 'hook'
        """
        log.msg("Run hook '%s'" % (name, ))

        try:
            hooks = cls._hooks[name]
        except KeyError, e:
            d = core.Deferred()
            d.callback(None)
            return d

        d = core.Deferred()
        print 'hooks are', hooks
        
        for p in hooks:
            fn = getattr(cls._plugin_instances[p], name)
            
            d.add_callback(return_or_call, fn, *args, **kwargs)
            
        #Kick off our chain of deferreds
        d.callback(None)
        return d

    def plugin_name(cls):
        return "%s.%s" % (cls.__module__, cls.__name__)

class Plugin:
    """
    Our base plugin class
    """
    __metaclass__ = PluginMount
    priority = 0

enable_plugin = Plugin.enable_plugin
disable_plugin = Plugin.disable_plugin
get_plugins = Plugin.get_plugins
get_active_plugins = Plugin.get_active_plugins
find_plugin_instance = Plugin.find_plugin_instance
run_hook = Plugin.run_hook
add_hook = Plugin.add_hook

def load_plugin_file(filename, failover_filename=None, min_priority=0,
        max_priority=None):
    """
    Load plugins from a file (able to restrict by priority). If the first file
    doesn't exist then the failover_filename is loaded. This is so that we can
    have a 'default' plugin file which can be optionally overwritten if another
    file exists.
    """
    
    fn = filename
    if not os.path.exists(filename):
        if failover_filename and os.path.exists(failover_filename):
            fn = failover_filename
        else:
            return
        
    with open(fn) as f:
        for line in f.readlines():
            line = line.strip()
            
            if line and not line.startswith("#"):
                priority, plugin = line.split(":")
                priority = int(priority)
                
                if not min_priority or priority > min_priority:
                    if not max_priority or priority < max_priority:
                        #Load this plugin
                        print 'loading plugin %s at priority %s' % (plugin, priority)
                        try:
                            util.import_class(plugin)
                            print 'enabling plugin %s' % (plugin, )
                            enable_plugin(plugin)
                        except:
                            log.err()

def load_start_plugins():
    log.msg("Loading plugins with priority < 10")
    load_plugin_file(get_plugin_file(), min_priority=-1, max_priority=10)
    load_plugin_file(get_builtin_plugin_file(), get_builtin_failover_file(),
            min_priority=-1, max_priority=10)

def load_second_plugins(*args):
    log.msg("Loading plugins with priority > 10")
    load_plugin_file(get_plugin_file(), min_priority=9)
    load_plugin_file(get_builtin_plugin_file(), get_builtin_failover_file(),
            min_priority=9)
    
    run_hook("on_plugins_loaded")

def get_plugin_file():
    return os.path.join(config.app_path, config.get('plugin_file', 'plugins.conf'))

def get_builtin_plugin_file():
    return os.path.join(config.app_path, config.get('plugin_file', 'builtin_plugins.conf'))

def get_builtin_failover_file():
    return os.path.join(os.path.dirname(config.__file__), 'builtin_plugins.conf')
