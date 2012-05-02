from gyro import core
from twisted.internet import reactor, task, defer
from twisted.python import log
from twisted.web import static, server
import sys #TODO: run logs through plugin

class TwistedLogger(object):
    """
    Redirect all standard twisted login to our log plugin system
    
    TODO: do this ;)
    """
    def __init__(self):
        log.startLogging(sys.stdout)

class TwistedCore(core.ICore):
    name = "Twisted Core"
    Deferred = defer.Deferred
    
    def run(self):
        TwistedLogger()
        return reactor.run()
        
    def call_later(self, delay, fn, *args, **kw):
        return reactor.callLater(delay, fn, *args, **kw)
        
    def defer_later(self, delay, fn, *args, **kw):
        return task.deferLater(reactor, delay, fn, *args,   **kw)
        
    def call_when_running(self, fn, *args, **kw):
        return reactor.callWhenRunning(fn, *args, **kw)
        
    def maybe_deferred(self, fn, *args, **kw):
        return defer.maybeDeferred(fn, *args, **kw)
        
    def call_on_shutdown(self, fn, *args, **kw):
        return reactor.addSystemEventTrigger('before', 'shutdown',
            fn, *args, **kw)
        
    def cancel_call_on_shutdown(self, call):
        return reactor.removeSystemEventTrigger(call)
        
TwistedCore.Deferred.add_callback = TwistedCore.Deferred.addCallback
TwistedCore.Deferred.add_errback = TwistedCore.Deferred.addErrback