from gyro import controller, auth

class Public(controller.Controller):
    """
    The publically accessible portion of our site
    """
    
    def error(self, request):
        raise Exception("foo!")
        
    def index(self, request):
        v = request.session.get("test", u"not from session")
        request.session["test"] = u"from session!"
        
        return self.render(request, {"test" : v})
        
@auth.secure()
class Private(controller.Controller):
    """
    Only logged in users can access this section
    """
    
    def dashboard(self, request):
        return self.render(request, {})
