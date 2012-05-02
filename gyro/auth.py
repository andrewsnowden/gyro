#-*- test-case-name: gyro.test.test_auth
"""
Web site authentication 
"""
from gyro import util, config, plugin

class secure(object):
    """
    A decorator for marking a controller as secured by an authentication
    provider
    """
    
    def __init__(self, provider=None):
        self.provider = provider
        
    def __call__(self, cls):
        if not self.provider:
            p = config.get("gyro-auth-provider", "gyro.auth.AuthProvider")
            provider = util.import_class(p)
            
            cls.auth_provider = provider
        else:
            cls.auth_provider = self.provider
            
        return cls

def authenticate(username, password, remember=False):
    """
    Authenticate/log in a user based on the given information
    """
    
    return plugin.run_hook("on_authenticate", username, password, remember)
    
class IAuthProvider(object):
    """
    A generic authentication provider
    """
    
    def get_user_session(self, uid):
        """
        Create a session map for the user described by the unique user
        identifier uid
        """
        raise NotImplementedError()

class AuthProvider(IAuthProvider):
    """
    The default authentication provider
    """
    
    def authenticate(self, username, password):
        return True
