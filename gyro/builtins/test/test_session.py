from twisted.trial import unittest
from gyro.builtins import session
from twisted.internet import defer
from gyro import core
from gyro.test import testutils

class SessionProviderTestCase(unittest.TestCase):
    def setUp(self):
        core.load("gyro.impl.twisted.core.TwistedCore")
        
    @defer.inlineCallbacks
    def test_cookie_load_store(self):
        sess = session.SessionProvider(storage=session.InMemorySessionStorage())
        request = testutils.FakeRequest()
        
        yield sess.on_before_render(request)
        
        self.assertEquals(request.session, {})
        self.assertNotEquals(request.session_uuid, None)
        
        #Set some things in session
        request.session["foo"] = "bar"
        
        sess.on_after_render(request)
        
        self.failUnless("gyro-session-uuid" in request.cookies)
        self.assertEquals(request.get_cookie("gyro-session-uuid"),
                          request.session_uuid)
        
        next_request = testutils.FakeRequest(cookies=dict(request.cookies))
        yield sess.on_before_render(next_request)
        
        self.assertEquals(next_request.session, {"foo":"bar"})
        self.assertEquals(next_request.session_uuid, request.session_uuid)
        