"""
Templates and functionality for standard account type operations
"""

from gyro import controller, plugin, auth, http, log
import os.path

class Account(controller.Controller):
    def __init__(self, path, auth_provider=None, default_next="/"):
        """
        TODO: allow to extend from different default template
        TODO: allow setting of own template and use the functionality
        TODO: allow customization for facebook/oauth logins?
        """

        self.path = path
        self.location = os.path.dirname(__file__)
        self.auth_provider = auth_provider or auth.AuthProvider
        self.default_next = default_next

        self.template_prefix = "gyro.account"
        self.template_location = os.path.join(self.location, "templates")

    def add_route(self, action):
        """
        Utility to add routes to actions contained in our controller
        """

        plugin.run_hook("on_add_route", "*", "%s%s" % (self.path, action),
                "gyro.builtins.account.account.Account.%s" % (action, ))

    def on_loaded(self):
        """
        Attach our routes and templates
        """

        plugin.run_hook("on_add_template_prefix", self.template_prefix,
                        self.template_location)

        self.add_route("login")
        self.add_route("logout")
        self.add_route("forgot")
        self.add_route("reset")

    def login(self, request):
        """
        Login page
        """
       
        kw = {}
        if "next" in request.args:
            kw["next"] = request.args["next"]

        if "email" in request.args:
            try:
                auth.authenticate(request.args["email"], request.args["email"],
                                  request.args.get("remember", False))
                _next = kw.get("next", self.default_next)
                if not _next:
                    _next = "/"

                return http.redirect(request, _next)
            except Exception, e:
                #TODO replace this with form generation and validation code
                log.err()
                kw["error"] = str(e)

        return self.render(request, kw)

    def logout(self, request):
        pass

    def forgot(self, request):
        pass

    def reset(self, request):
        pass
