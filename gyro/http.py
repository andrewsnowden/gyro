"""
HTTP response codes and helpers
"""

OK                              = 200
CREATED                         = 201
ACCEPTED                        = 202
NON_AUTHORITATIVE_INFORMATION   = 203
NO_CONTENT                      = 204
RESET_CONTENT                   = 205
PARTIAL_CONTENT                 = 206
MULTI_STATUS                    = 207

MULTIPLE_CHOICE                 = 300
MOVED_PERMANENTLY               = 301
FOUND                           = 302
SEE_OTHER                       = 303
NOT_MODIFIED                    = 304
USE_PROXY                       = 305
TEMPORARY_REDIRECT              = 307

BAD_REQUEST                     = 400
UNAUTHORIZED                    = 401
PAYMENT_REQUIRED                = 402
FORBIDDEN                       = 403
NOT_FOUND                       = 404
NOT_ALLOWED                     = 405
NOT_ACCEPTABLE                  = 406
PROXY_AUTH_REQUIRED             = 407
REQUEST_TIMEOUT                 = 408
CONFLICT                        = 409
GONE                            = 410
LENGTH_REQUIRED                 = 411
PRECONDITION_FAILED             = 412
REQUEST_ENTITY_TOO_LARGE        = 413
REQUEST_URI_TOO_LONG            = 414
UNSUPPORTED_MEDIA_TYPE          = 415
REQUESTED_RANGE_NOT_SATISFIABLE = 416
EXPECTATION_FAILED              = 417

INTERNAL_SERVER_ERROR           = 500
NOT_IMPLEMENTED                 = 501
BAD_GATEWAY                     = 502
SERVICE_UNAVAILABLE             = 503
GATEWAY_TIMEOUT                 = 504
HTTP_VERSION_NOT_SUPPORTED      = 505
INSUFFICIENT_STORAGE_SPACE      = 507
NOT_EXTENDED                    = 510

def redirect(request, location):
    request.set_response_code(FOUND)
    request.set_header("location", location)
    print dir(request)
    print 'headers', request.headers
    return """<html>
    <head>
        <meta http-equiv=\"refresh\" content=\"30;URL=%(url)s\">
    </head>
    <body><a href=\"%(url)s\">click here</a></body></html>
""" % {'url': location}
