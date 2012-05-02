"""
A plugin that offers Jinja2 templating
"""

#-*- test-case-name: gyro.builtins.test.test_jinja
from gyro import plugin, config
import os.path
import jinja2

class JinjaLoader(jinja2.BaseLoader):
    def __init__(self, default=None, delimiter='/'):
        self.mapping = {}
        self.default = default
        self.delimiter = delimiter
        
    def get_source(self, environment, template):
        try:
            prefix, name = template.split(self.delimiter, 1)
            loader = self.mapping[prefix]
        except (ValueError, KeyError):
            return self.default.get_source(environment, template)
        
        try:
            return loader.get_source(environment, name)
        except jinja2.TemplateNotFound:
            raise jinja2.TemplateNotFound(template)

class JinjaEngine(plugin.Plugin):
    """
    A templating engine to render Jinja2 templates
    """
    
    def __init__(self):
        self.template_path = os.path.join(config.app_path, "templates")
        self.loader = JinjaLoader(jinja2.FileSystemLoader(self.template_path))
        self.env = jinja2.Environment(loader=self.loader)
        
    def on_add_template_prefix(self, prefix, location):
        """
        Add a template location with the given prefix
        """
        print 'add template location', prefix, location
        self.loader.mapping[prefix] = jinja2.FileSystemLoader(location)
        
    def on_render_template(self, request, template, context):
        """
        The default render method
        """
        print '>>> on_render_template'
        print 'template is', template
        
        t = self.env.get_template(template)
        return t.render(context).encode("utf-8")
        
    def on_render_jinja2_template(self, request, template, context):
        """
        A specialized Jinja2 render method to use in case jinja2 is not the
        highest priority for on_render_template
        """
        return self.on_render_template(request, template, context)
