"""
A plugin to handle 'development' mode for Gyro.
"""

from gyro import plugin, config, log
from twisted.internet import defer
import threading
import os
import sys
import time
import traceback

def get_code_preview(filename, line_no):
    """
    Extract a portion of code from a file to display as a code preview
    """
    with open(filename) as f:
        lines = f.readlines()
        
        for ln in range(max(0, line_no - 2), min(line_no+1, len(lines))):
            yield ln + 1, lines[ln]

class DevelopmentMode(plugin.Plugin):
    """
    This plugin provides auto-restarting of Gyro when code has changed. It
    does this in a way that avoids continous restarts by deferring the loading
    of code until an actual web request has been processed. This behaviour
    can be disabled by setting the configuration parameter gyro-smart-reload
    to False
    """
    
    def __init__(self):
        self.smart_reload = config.get("gyro-smart-reload", True)
        self.poll_interval = config.get("gyro-reload-poll-interval", 3)
        self.had_first_request = False
        self.watch_files = []
        self.module_mtimes = {}
        self.location = os.path.dirname(__file__)
        
        if config.development and not self.smart_reload:
            self.start_monitoring()
            
    def on_first_request(self, request):
        self.had_first_request = True
        
        if config.development:
            if self.smart_reload:
                plugin.load_second_plugins()
                self.start_monitoring()
                
            self.template_prefix = "gyro.development"
            self.template_location = os.path.join(self.location, "templates")
            
            j = plugin.find_plugin_instance("jinja.JinjaEngine")
            plugin.run_hook("on_add_template_prefix", self.template_prefix,
                            self.template_location)
                
    def start_monitoring(self):
        #Launch a thread to do file monitoring
        t = threading.Thread(target=self.monitor_changes)
        t.setDaemon(True)
        t.start()

    def monitor_changes(self):
        while True:
            filename = self.check_reload()
            
            if filename:
                #A file has changed
                if self.smart_reload:
                    if self.had_first_request:
                        #Only restart if we have had our first request
                        print >> sys.stderr, ("%s changed; reloading..." %
                                filename)
                        os._exit(3)
                else:
                    print >> sys.stderr, ("%s changed; reloading..." %
                            filename)
                    os._exit(3)
                break
            time.sleep(self.poll_interval)
            
    def check_reload(self):
        filenames = list(self.watch_files)
        for module in sys.modules.values():
            try:
                filename = module.__file__
            except (AttributeError, ImportError), exc:
                continue
            if filename is not None:
                filenames.append(filename)
        for filename in filenames:
            try:
                stat = os.stat(filename)
                if stat:
                    mtime = stat.st_mtime
                else:
                    mtime = 0
            except (OSError, IOError):
                continue
            if filename.endswith('.pyc') and os.path.exists(filename[:-1]):
                mtime = max(os.stat(filename[:-1]).st_mtime, mtime)
            elif (filename.endswith('$py.class') and
                    os.path.exists(filename[:-9] + '.py')):
                mtime = max(os.stat(filename[:-9] + '.py').st_mtime, mtime)
            if not self.module_mtimes.has_key(filename):
                self.module_mtimes[filename] = mtime
            elif self.module_mtimes[filename] < mtime:
                return filename

    @defer.inlineCallbacks
    def on_route_not_found(self, request):
        routes = yield plugin.run_hook("on_list_routes")
        
        ctx = {
            "path" : request.path,
            "routes" : routes,
        }
        
        t = yield plugin.run_hook("on_render_jinja2_template", request,
                               "gyro.development/404.html", ctx)
        request.set_response_code(404)
        request.set_header("content-type", "text/html")
        request.write(t.encode("utf-8"))
        request.finish()
        defer.returnValue(request)
    
    @defer.inlineCallbacks
    def on_error_rendering(self, request, f):
        frames = f.stack[-5:] + f.frames
        traceback = []
        
        for fn, filename, line_no, loc, glob in frames:
            traceback.append({
                "fn" : fn,
                "filename" : filename,
                "line_no" : line_no,
                "preview" : get_code_preview(filename, line_no)
            })
            
        ctx = {
            "failure" : f,
            "traceback" : traceback,
            "error" : "%s.%s : %s" % (f.type.__module__, f.type.__name__, f.value)
        }
        
        t = yield plugin.run_hook("on_render_jinja2_template", request,
                               "gyro.development/500.html", ctx)
        
        if not t:
            #Our 500 page didn't get rendered
            log.msg("Error rendering 500 template")
            t = "<html><body><pre>%s</pre></body></html>" % (f.getTraceback(), )
            
        request.set_response_code(500)
        request.set_header("content-type", "text/html")
        request.write(t.encode("utf-8"))
        request.finish()
        defer.returnValue(request)
        
