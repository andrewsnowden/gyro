#-*- test-case-name: gyro.builtins.test.test_auth
"""
User authentication
"""
from gyro import plugin, util, config, core
from twisted.internet import defer
import datetime

class InMemoryAuthTokenStorage(object):
    """
    In memory storage of authentication tokens. Not all that practical but
    useful for testing
    """
    def __init__(self, tokens=None):
        self.tokens = tokens or {}
        
    def use_token(self, token):
        try:
            return self.tokens.pop(token)
        except KeyError:
            return None
        
    def add_token(self, token, uid):
        self.tokens[token] = uid
        
class CookieTokenAuthentication(plugin.Plugin):
    """
    Provid 'remember me' functionality by using an authentication token which
    allows a session to get automatically created
    """
    
    def __init__(self, storage=None):
        if not storage:
            s = config.get("gyro-auth-token-storage",
                           "gyro.builtins.auth.InMemoryAuthTokenStorage")
            self.storage = util.import_class(s)()
        else:
            self.storage = storage
            
        self.token_valid_time = datetime.timedelta(days=config.get(
            "gyro-auth-token-timeout", 90))
        
    @defer.inlineCallbacks
    def on_remember_me(self, request, uid, token=None, cookie_name=None):
        """
        Remember a user's authentication information so that they don't have
        to log in every time their session expires
        """
        token = token or util.uuid()
        cookie_name = cookie_name or request.get_action_parameter(
            "auth_token_cookie_name", "gyro-auth-token")
        
        yield core.maybe_deferred(self.storage.add_token,
                                   token, uid)
        
        request.add_cookie(cookie_name, token,
                           expires=datetime.datetime.now() +
                           self.token_valid_time, path="/")
    
    @defer.inlineCallbacks
    def on_new_session(self, request):
        """
        We are about to create a new session for this user. Should we
        automagically authenticate him based on an authentication token and then
        use this information to generate the session
        """
        
        cookie_name = request.get_action_parameter("auth_token_cookie_name",
                                                  "gyro-auth-token")
        token = request.get_cookie(cookie_name)
        
        if token:
            uid = yield core.maybe_deferred(self.storage.use_token, token)
            
            if uid:
                engine = request.get_action_parameter("auth_provider")
                
                if engine:
                    session = yield core.maybe_deferred(engine.get_user_session,
                                                        uid)
                
                    if session:
                        self.on_remember_me(request, uid, token, cookie_name)
                        defer.returnValue(session)
            
