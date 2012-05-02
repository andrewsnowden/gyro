#-*- test-case-name: gyro.builtins.test.test_router
from gyro import plugin, config, controller, log
import gyro
import routes
import os.path

class RoutesRouter(plugin.Plugin):
    """
    A router that uses the routes module to perform routing:
    See http://routes.groovie.org/ for more details
    """
    
    def __init__(self, lines=None):
        self.map = routes.Mapper()
        
        if lines:
            self.load_lines(lines)
            
    def on_plugins_loaded(self):
        #Read from our routes file
        builtin = config.get_project_file("builtin-routes-file",
                                          "builtin-routes.conf")
        if not os.path.exists(builtin):
            builtin = os.path.join(os.path.dirname(gyro.__file__),
                                   "builtin_routes.conf")
            
        with open(builtin) as f:
            lines = f.readlines()
            
        self.load_lines(lines)
        
        rf = config.get_project_file("routes-file", "routes.conf")
    
        with open(rf) as f:
            lines = f.readlines()
            
        self.load_lines(lines)
        
    def load_lines(self, lines):
        for line in lines:
            line = line.strip()
            if not line.startswith("#") and line:
                method, path, pg = (x.strip() for x in line.split())
                try:
                    self.on_add_route(method, path, pg, update=False)
                except:
                    log.err()
                
        self.map.create_regs()
        
    def on_add_route(self, method, path, pg, update=True):
        kw = {}
        
        if method != "*":
            kw["conditions"] = dict(method=[method])
            
        if pg.startswith("static-dir"):
            directory = pg.split(":", 1)[1]
            
            kw["controller"] = "gyro.controller.StaticDirectory"
            kw["action"] = "serve"
            kw["directory"] = directory
            self.map.connect(pg, path, **kw)
        elif pg.startswith("module:"):
            c = pg.split(":", 1)[1]
            controller.load_class(c, path)
        else:
            kw["controller"], kw["action"] = pg.rsplit(".", 1)
            controller.load_class(kw["controller"])
            self.map.connect(pg, path, **kw)
            
        
        if update:
            self.map.create_regs()
                    
    def on_route_request(self, request):
        if not request.path:
            request.path = "/"
            
        kw = self.map.match(request.path)
        
        if kw:
            c, a = kw["controller"], kw["action"]
            request.kw = kw
            return controller.get_action(c, a)

    def on_list_routes(self):
        """
        Return a list of routes to display in our development 404 page
        """
        return [(x.routepath, str(x.defaults)) for x in self.map.matchlist]