from twisted.web import http, server, static
from twisted.internet import reactor, endpoints, protocol
from gyro import core
import gyro.server
import datetime

class TwistedRequest(http.Request, gyro.server.IRequest):
    """
    Bridge the gap between a Twisted http.Request and a Gyro Request
    """
    def process(self):
        self._args = self.args
        self.args = {}

        #We don't want to have to deal with args being a list
        for k, v in self._args.iteritems():
            if len(v) > 1:
                self.args[k] = v
            else:
                self.args[k] = v[0]

        self.set_header("server", "Gyro Twisted")
        self.set_header('date', http.datetimeToString())
        core.server.process_request(self)
        return server.NOT_DONE_YET

    set_header = http.Request.setHeader
    get_header = http.Request.getHeader
    get_cookie = http.Request.getCookie
    set_response_code = http.Request.setResponseCode

    def add_cookie(self, k, v, expires=None, **kwargs):
        if isinstance(expires, datetime.datetime):
            expires = expires.strftime("%s, %d %b %Y %H:%M:%S")

        return self.addCookie(k, v, expires=expires, **kwargs)

class HTTPChannel(http.HTTPChannel):
    requestFactory = TwistedRequest

class HTTPFactory(protocol.ServerFactory):
    protocol = HTTPChannel

    def __init__(self, timeout=60*60*12):
        self.timeOut = timeout

    def buildProtocol(self, addr):
        p = protocol.ServerFactory.buildProtocol(self, addr)
        p.timeOut = self.timeOut
        return p

    def log(self, request):
        print 'request', request

class HttpServer(gyro.server.HttpServer):
    listeningPort = None

    def run(self, port):
        print 'Start HTTP server on port %s' % (port, )
        self.factory = HTTPFactory()
        self.endpoint = endpoints.serverFromString(reactor, "tcp:%s" % (port, ))

        def cbListen(result):
            self.listeningPoint = result

        self.endpoint.listen(self.factory).addCallback(cbListen)

    def stop(self):
        self.listeningPort.stopListening()

    def serve_static(self, request, filename):
        f = static.File(filename)
        r = f.render_GET(request)
        if r != server.NOT_DONE_YET:
            request.write(r)
            request.finish()
