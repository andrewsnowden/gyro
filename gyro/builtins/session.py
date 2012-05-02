#-*- test-case-name: gyro.builtins.test.test_session
"""
HTTP Sessions
"""

from gyro import plugin, util, config
import datetime
from uuid import uuid1

def generate_uuid():
    return uuid1().hex

class InMemorySessionStorage(object):
    """
    The simplest way to do sessions - store everything in memory. This isn't
    persistant so isn't a great way to do it
    """
    #TODO expire
    
    def __init__(self):
        self.sessions = {}
        
    def get_session(self, uuid):
        return self.sessions.get(uuid, None)
    
    def set_session(self, uuid, session):
        self.sessions[uuid] = session

class SessionProvider(plugin.Plugin):
    def __init__(self, storage=None):
        if not storage:
            s = config.get("gyro-session-storage",
                    "gyro.builtins.session.InMemorySessionStorage")
            self.storage = util.import_class(s)()
        else:
            self.storage = storage
            
        self.session_timeout = datetime.timedelta(hours=config.get(
            "gyro-session-timeout", 24))
    
    def on_before_render(self, request):
        """
        Load our session before rendering a request
        """
        
        cookie_name = request.get_action_parameter("session_cookie_name",
                                                  "gyro-session-uuid")
        uuid = request.get_cookie(cookie_name)
        
        session = None
        
        if uuid:
            session = self.storage.get_session(uuid)
        else:
            uuid = generate_uuid()
            
        request.session_uuid = uuid
        
        if session is not None:
            request.session = session
        else:
            def set_session(r):
                if not r:
                    r = {}
                    
                request.session = r
                
            return plugin.run_hook("on_new_session", request).add_callback(
                set_session)
            
    def write_session_cookie(self, request):
        """
        Write our session cookie to this request
        """
        expires = datetime.datetime.now() + self.session_timeout
        
        cookie_name = request.get_action_parameter("session_cookie_name",
                                                  "gyro-session-uuid")
        request.add_cookie(cookie_name, request.session_uuid,
                          expires=expires, path="/")

    def on_after_render(self, request):
        """
        After we have finished processing this request we need to save our
        updated session and write the cookie to the request's response
        """
        self.write_session_cookie(request)
        return self.storage.set_session(request.session_uuid, request.session)
