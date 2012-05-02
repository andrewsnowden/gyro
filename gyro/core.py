"""
Although Gyro uses Twisted by default, it does so through this core interface
which allows for other event frameworks to be substituted in. All they must do
is provide the functionality that Gyro relies on to work properly, all of
this functionality is defined here
"""

import sys
from gyro import util

class CoreError(Exception):
    pass

CORE = None

class ICore(object):
    """
    A framework core. To switch out Twisted, a framework must implement all the
    methods in this interface
    """
    
    name = "Core Interface"
    Deferred = None #An implementation of a Twisted Deferred
    first_request = True
    
    def __str__(self):
        return "ICore(%s)" % (self.name, )
    
    def run(self):
        """
        
        Start the core
        """
        pass
    
    def call_later(self, delay, callab, *args, **kwargs):
        """
        Call this function after a number of seconds
        """
        pass
    
    def defer_later(self, seconds, fn, *args, **kwargs):
        """
        Call this function after a number of seconds and return the result as a
        deferred
        """
        
    def call_when_running(self, fn, *args, **kwargs):
        """
        Call this function when the core is up and running
        """
        
    def call_on_shutdown(self, fn, *args, **kwargs):
        """
        Call this function when the core is shutting down
        """
        
    def cancel_call_on_shutdown(self, call):
        """
        Cancel the function that was supposed to be called on shutdown. Call is
        the result that was returned by the call_on_shutdown command
        """
        
    def maybe_deferred(self, fn, *args, **kwargs):
        """
        Even if this function doesn't return a deferred, wrap it in a deferred
        so that we can treat it as a deferred
        """
        
    def servce_static(self, request, filename):
        """
        Serve a static file. This probably needs to be done by the core because
        with asynchronous frameworks it needs to do it in an asynchronous way
        """
        
def load(core_string):
    """
    Load a core
    """
    
    c = util.import_class(core_string)()
    
    core = sys.modules.get("gyro.core")
    core.Deferred = c.Deferred
    core.run = c.run
    core.call_later = c.call_later
    core.defer_later = c.defer_later
    core.call_when_running = c.call_when_running
    core.call_on_shutdown = c.call_on_shutdown
    core.cancel_call_on_shutdown = c.cancel_call_on_shutdown
    core.maybe_deferred = c.maybe_deferred
    
    global CORE
    CORE = c

def not_loaded(*args, **kwargs):
    raise CoreError("Core has not been loaded")

Deferred = not_loaded
run = not_loaded
call_later = not_loaded
defer_later = not_loaded
call_when_running = not_loaded
call_on_shutdown = not_loaded
cancel_call_on_shutdown = not_loaded
maybe_deferred = not_loaded
