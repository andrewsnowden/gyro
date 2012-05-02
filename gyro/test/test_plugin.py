from twisted.trial import unittest
from twisted.internet import defer
from gyro import plugin, core

class PluginTestCase(unittest.TestCase):
    def setUp(self):
        """
        Clear our plugin system before each test
        """
        
        plugin.Plugin.clear()

    def test_parse_plugin_file(self):
        raise unittest.SkipTest("not written yet")
        
    def test_register_and_activate(self):
        """
        Make sure our plugin appears in get_plugins and that we can enable
        and disable it
        """
        
        class ExamplePlugin(plugin.Plugin):
            pass

        #Check it is in available plugins, but is not in active plugins
        self.failUnless(ExamplePlugin in plugin.Plugin.get_plugins())
        self.failUnless(ExamplePlugin not in plugin.Plugin.get_active_plugins())

        #Check we can enable it
        plugin.Plugin.enable_plugin('gyro.test.test_plugin.ExamplePlugin')
        self.failUnless(ExamplePlugin in plugin.Plugin.get_active_plugins())

        #Check we can disable it
        plugin.Plugin.disable_plugin('ExamplePlugin')
        self.failUnless(ExamplePlugin not in plugin.Plugin.get_active_plugins())
        
    @defer.inlineCallbacks
    def test_run_hooks(self):
        """
        Check that we execute hooks correctly according to priority and that
        the execution chain is correct based on return result. Note that this
        only tests synchronous hooks
        """
        
        core.load("gyro.impl.twisted.core.TwistedCore")
        
        class HighPriorityPlugin(plugin.Plugin):
            priority = 0

            def on_high(self, arg):
                return "high" + arg

            def on_medium(self, arg):
                return None

            def on_low(self, arg):
                return None

        class MediumPriorityPlugin(plugin.Plugin):
            priority = 50

            def on_high(self, arg):
                return "medium" + arg

            def on_medium(self, arg):
                return "medium" + arg

            def on_low(self, arg):
                return None

        class LowerPriorityPlugin(plugin.Plugin):
            priority = 100

            def on_high(self, arg):
                return "low" + arg

            def on_medium(self, arg):
                return "low" + arg

            def on_low(self, arg):
                return "low" + arg

        self.failUnless(HighPriorityPlugin in plugin.Plugin.get_plugins())
        self.failUnless(MediumPriorityPlugin in plugin.Plugin.get_plugins())
        self.failUnless(LowerPriorityPlugin in plugin.Plugin.get_plugins())

        plugin.enable_plugin("HighPriorityPlugin")
        plugin.enable_plugin("MediumPriorityPlugin")
        plugin.enable_plugin("LowerPriorityPlugin")

        self.assertEquals(len(plugin.get_active_plugins()), 3)

        r = yield plugin.run_hook("on_high", "result")
        self.assertEquals(r, "highresult")
        r = yield plugin.run_hook("on_medium", "result")
        self.assertEquals(r, "mediumresult")
        r = yield plugin.run_hook("on_low", "result")
        self.assertEquals(r, "lowresult")
        
        plugin.disable_plugin("HighPriorityPlugin")
        r = yield plugin.run_hook("on_high", "result")
        self.assertEquals(r, "mediumresult")

    @defer.inlineCallbacks
    def test_deferred_hooks(self):
        """
        Test that our plugins can return deferreds as part of their hooks and
        that we run the plugin chain correctly based on the result of these
        deferreds
        """
        
        core.load("gyro.impl.twisted.core.TwistedCore")
        
        class FirstPlugin(plugin.Plugin):
            priority = 0
            
            def on_first(self, arg):
                return core.defer_later(0.01, lambda: "first" + arg)
                
            def on_second(self, arg):
                return core.defer_later(0.01, lambda: None)
                
        class SecondPlugin(plugin.Plugin):
            priority = 0
            
            def on_first(self, arg):
                raise AssertionError("Should not be called")
            
            def on_second(self, arg):
                return core.defer_later(0.01, lambda: "second" + arg)
                
        plugin.enable_plugin("FirstPlugin")
        plugin.enable_plugin("SecondPlugin")
        
        self.assertEquals(len(plugin.get_active_plugins()), 2)
        
        r = yield plugin.run_hook("on_first", "result")
        self.assertEquals(r, "firstresult")
        
        r = yield plugin.run_hook("on_second", "result")
        self.assertEquals(r, "secondresult")
        
    @defer.inlineCallbacks
    def test_temporary_hook(self):
        def temp(p, arg):
            return 'temp' + arg
        
        plugin.add_hook("on_temp", temp)
        
        r = yield plugin.run_hook("on_temp", "result")
        self.assertEquals(r, "tempresult")
