#-*- test-case-name: gyro.builtins.test.test_render
from gyro import plugin, core, log

class DeferredRenderer(plugin.Plugin):
    def on_render_request(self, request):
        """
        Action will return a Deferred that will return the page content
        """
        def cb_action(result):
            request.set_header('content-length', str(len(result)))
            
            def _write(r):
                request.write(result)
                return True
            
            return plugin.run_hook("on_after_render", request
                                  ).add_callback(_write)
            
        #TODO execute a before/after hook if one exists in the controller
        
        """
        #TODO pass in args as *args and **kwargs
        if not self.args:
            self.args = inspect.getargspec(self.rend)

        for index, arg in enumerate(self.args.args):
            if arg in self.request.args:
                kw[arg] = self.request.args[arg]
            else:
                #If it doesn't have a default, pass in None
                if self.args.defaults and len(self.args.defaults) + index < len(self.args):
                    kw[arg] = None
        """
        
        print 'request.action', request.action
        return core.maybe_deferred(request.action, request).add_callback(cb_action)
        
    def on_render_basic(self, request):
        """
        Just call action and let it do what it needs to do
        """
        return core.maybe_deferred(request.action, request)
        
    def on_route_not_found(self, request):
        #TODO pretty 404 page
        #TODO custom settable 404 page
        request.set_response_code(404)
        request.set_header("content-type", "text/html")
        request.write("Not Found")
        return request
        
    def on_error_rendering(self, request, f):
        #TODO pretty error page
        #TODO custom settable error page
        log.err(f)
        request.set_response_code(500)
        request.set_header("content-type", "text/html")
        request.write("<html><body>%s</body></html>" % (f))
        return request
