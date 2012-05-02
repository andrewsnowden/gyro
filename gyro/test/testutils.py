"""
Classes that are useful for testing Gyro
"""

from gyro import controller, server

class FakeAuthProvider(object):
    def get_user_session(self, uid):
        return {
            "uid" : uid,
        }

class FakeController(controller.Controller):
    auth_provider = FakeAuthProvider()
    
    def foo(self, request):
        pass

class FakeRequest(server.IRequest):
    def __init__(self, cookies=None, **kwargs):
        self.cookies = cookies or {}
        
        self.controller = FakeController()
        self.action = self.controller.foo
        
        for k, v in kwargs.items():
            self.k = v
        
    def get_cookie(self, name, *args, **kwargs):
        return self.cookies.get(name, None)
    
    def add_cookie(self, name, value, *args, **kwargs):
        self.cookies[name] = value
    