from twisted.trial import unittest
from twisted.internet import defer

from gyro.builtins import auth
from gyro.test import testutils
from gyro import core

class CookieTokenTestCase(unittest.TestCase):
    def setUp(self):
        core.load("gyro.impl.twisted.core.TwistedCore")
    
    @defer.inlineCallbacks
    def test_token_authentication(self):
        storage = auth.InMemoryAuthTokenStorage()
        c = auth.CookieTokenAuthentication(storage)
        
        request = testutils.FakeRequest()
        yield c.on_remember_me(request, "1234")
        
        self.assertEquals(len(request.cookies), 1)
        token = request.cookies["gyro-auth-token"]
        self.assertNotEqual(token, None)
        
        next_request = testutils.FakeRequest(
            cookies={"gyro-auth-token" : token})
        
        session = yield c.on_new_session(next_request)
        self.assertEquals(session, {"uid" : "1234"})
