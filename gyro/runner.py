"""
Run the main Gyro application
"""

import os.path
import os
import sys
from gyro import config, core, util, plugin

def run(path, daemonize=False, development=False, **kwargs):
    if not path:
        path = os.getcwd()

    config.load(os.path.join(path, 'app.conf'))

    config.app_path = path
    config.app_name = path.rsplit("/", 1)[1]
    config.development = development
    config.daemonize = daemonize

    sys.path.append(config.app_path)

    core.load(config.get("core", "gyro.impl.twisted.core.TwistedCore"))

    plugin.load_start_plugins()

    core.call_when_running(start, **kwargs)
    core.run()

def start(**kwargs):
    """
    Start our HTTP server
    """
    s = config.get('server', 'gyro.impl.twisted.server.HttpServer')
    port = kwargs.get("port", None)
    if not port:
        port = config.get("port", 9999)

    server = util.import_class(s)
    print 'Starting server %s on port %s' % (server, port)
    core.server = server()
    core.server.run(port)

    if not config.development and config.get("gyro-smart-reload", True):
        plugin.load_second_plugins()
