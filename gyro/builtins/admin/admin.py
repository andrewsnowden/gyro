from gyro import controller, plugin
import os.path

class Admin(controller.Controller):
    def __init__(self, path):
        self.path = path
        self.location = os.path.dirname(__file__)
        
        self.template_prefix = "gyro.admin"
        self.template_location = os.path.join(self.location, "templates")
        
    def on_loaded(self):
        plugin.run_hook("on_add_route", "*", self.path, self.get_action("index"))
        
        plugin.run_hook("on_add_template_prefix", self.template_prefix,
                        self.template_location)
        
    def sub_path(self, sub):
        return "%s/%s" % (self.path, sub)
        
    def get_action(self, action):
        return "gyro.builtins.admin.admin.Admin.%s" % (action, )
        
    def index(self, request):
        return self.render(request, {"foo" : u"foo!"})
