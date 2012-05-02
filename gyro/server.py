"""
HTTP Request and Response classes, utilities and functions
"""
from gyro import plugin, core

class IRequest(object):
    """
    A generic request object that can be used by Gyro and its plugins to
    process this request
    
    This is provided for reference and 
    """
    
    #TODO actually do this instead of just using Twisted's Request
    #We will need to refactor the names of all the things like
    #getHeader, setResponseCode that are already used
    
    method = None #GET/POST/HEAD
    uri = None #Full URI string
    path = None #Just the path (no params)
    content = None
    host = None
    
    def set_header(self, name, value):
        raise NotImplementedError()
    
    def get_header(self, name):
        raise NotImplementedError()
    
    def add_cookie(self, k, v, expires=None, domain=None, path=None,
                   max_age=None, comment=None, secure=None):
        raise NotImplementedError()
    
    def get_cookie(self, key):
        raise NotImplementedError()
        
    def set_response_code(self, code, message=None):
        raise NotImplementedError()
    
    def write(self, data):
        raise NotImplementedError()
    
    def finish(self):
        raise NotImplementedError()
    
    def get_action_parameter(self, name, default=None):
        """
        Get a parameter that is set either at a controller or an action
        level
        """
        
        param = getattr(self.action, name, None)
        if not param:
            param = getattr(self.action.im_class, name, default)
            
        return param
    
class HttpServer(object):
    """
    A base class for an HTTP server that knows how to process a request once
    it has come in
    """
    
    first_request = True
    
    def process_request(self, request):
        """
        Process a request and execute all of the hooks surrounding it.
        Generally a web server woudln't want to modify this method but can if
        the flow of a request needs to change for some reason
        
        Unfortunately this is a bit rough to read because I didn't want to
        have to introduce a dependency on inlineCallbacks which would make
        it a lot nicer. Read it from the bottom up
        """
        
        def _finish(result):
            request.finish()
        
        def _after(result):
            return plugin.run_hook('on_finished_request', request).add_callback(
                _finish)
            
        def _render(result):
            renderer = getattr(request.action.im_class, "renderer", "on_render_request")
            return plugin.run_hook(renderer, request).add_callback(_after)
            
        def _routed(action):
            if not action:
                return plugin.run_hook('on_route_not_found', request)
                
            request.action = action
            return plugin.run_hook('on_before_render', request).add_callback(_render)
            
        def _route(result):
            return plugin.run_hook('on_route_request', request).add_callback(_routed)
            
        def _new(result=None):
            return plugin.run_hook("on_new_request", request).add_callback(_route)
            
        def _process():
            if self.first_request:
                self.first_request = False
                return plugin.run_hook("on_first_request", request).add_callback(_new)
                
            return _new()
            
        def _eb_process(f):
            print f
            try:
                return plugin.run_hook("on_error_rendering", request, f
                                      ).add_callback(_finish)
            except:
                log.err(f)
        
        return _process().add_errback(_eb_process)

    def serve_static(self, request, filename):
        """
        Serve a static file. For asynchronous reactors like Twisted, we should
        do this in an asynchronous friendly way so no default implementation is
        provided
        """
        
        raise NotImplementedError()