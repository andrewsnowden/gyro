"""
A controller is a group of functions that are responsible for rendering pages.
They share common attributes like security requirements, or can just be a
logical grouping of pages
"""

from gyro import util, config, plugin, core, log
import gyro
import os.path

class Controller(object):
    """
    A group of actions that will generate pages
    """
    
    def render(self, request, context, template=None):
        """
        Render a page using the default templating engine given the context and
        template
        """
        
        cls = request.action.im_class
        
        if not template:
            template = "%s.html" % (request.action.im_func.func_name)
            
        prefix = getattr(self, "template_prefix", None)
        if prefix:
            template = "%s/%s" % (prefix, template)
        r = getattr(self, "template_hook", "on_render_template")
        return plugin.run_hook(r, request, template, context)
        
    def on_loaded(self):
        """
        Run after we have been loaded
        """
        
class StaticDirectory(Controller):
    """
    A controller to serve static files
    """
    renderer = "on_render_basic"
    
    def serve(self, request):
        print 'serve static', request.kw
        attempts = [
            os.path.join(config.app_path, request.kw["directory"],
                         request.kw["filename"]),
            os.path.join(request.kw["directory"], request.kw["filename"]),
            os.path.join(os.path.dirname(gyro.__file__), "builtins",
                         request.kw["directory"], request.kw["filename"]),
        ]
        
        for attempt in attempts:
            if os.path.exists(attempt):
                return core.server.serve_static(request, attempt)
        
        return plugin.run_hook("on_route_not_found", request)
        
controllers = {}

def load_class(controller, *args, **kwargs):
    """
    Load the class given by the string 'controller'
    """
    
    if controller in controllers:
        return controllers[controller]
        
    attempts = [
        controller,
        "%s.%s" % (config.app_name, controller),
        "%s.controllers.%s" % (config.app_name, controller),
        "gyro.%s" % (controller, ),
        "gyro.builtins.%s" % (controller, ),
        "gyro.builtins.%s.%s" % (controller, controller),
    ]
    
    common = set(attempts).intersection(controllers.keys())
    
    if common:
        c = controllers[list(common)[0]]
        return c
    
    for attempt in attempts:
        try:
            cls = util.import_class(attempt)
            controllers[attempt] = cls(*args, **kwargs)
            controllers[attempt].on_loaded()
            return controllers[attempt]
        except ImportError:
            pass
        
    raise ImportError("Unable to find import for %s" % (controller, ))

def get_action(controller, action):
    """
    Given a string name that resolves to a controller/action, return the
    bound instance method for this action
    """
    
    if controller not in controllers:
        return getattr(load_class(controller), action)
    
    return getattr(controllers[controller], action)
