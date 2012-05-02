from twisted.trial import unittest
from gyro.builtins import router
from gyro import controller, config

class TestController(controller.Controller):
    def first_page(self, request):
        pass
    
    def second_page(self, request):
        pass
    
class AnotherController(controller.Controller):
    def first_page(self, request):
        pass

class FakeRequest(object):
    def __init__(self, path, method="GET"):
        self.path = path
        self.method = "GET"

class RoutesTestCase(unittest.TestCase):
    def setUp(self):
        config.app_name = "gyro"
        
    def test_simple(self):
        routes = [
            "*\t/\tgyro.builtins.test.test_router.TestController.first_page",
            "*\t/home\tgyro.builtins.test.test_router.TestController.second_page",
            "*\t/foo/bar\tgyro.builtins.test.test_router.AnotherController.first_page",
        ]
        
        r = router.RoutesRouter(lines=routes)
        
        #Test /
        fn = r.on_route_request(FakeRequest("/"))
        self.assertEquals(fn.im_class, TestController)
        self.assertEquals(fn.im_func.func_name, 'first_page')
        
        #Test /home
        fn = r.on_route_request(FakeRequest("/home"))
        self.assertEquals(fn.im_class, TestController)
        self.assertEquals(fn.im_func.func_name, 'second_page')
        
        #Test /foo/bar
        fn = r.on_route_request(FakeRequest("/foo/bar"))
        self.assertEquals(fn.im_class, AnotherController)
        self.assertEquals(fn.im_func.func_name, 'first_page')
        
        #Test /foo/bar/
        p = r.on_route_request(FakeRequest("/foo/bar/"))
        self.assertEquals(p, None)
        
        p = r.on_route_request(FakeRequest("/quux"))
        self.assertEquals(p, None)
