from twisted.trial import unittest
from gyro import config
import StringIO

class ConfigTestCase(unittest.TestCase):
    def test_parse_config(self):
        """
        The common types of things we would be setting/getting from our config
        """
        f = StringIO.StringIO("nospace=test1\n"
                "space = test2 \n"
                "quoted = 'test3 '\n"
                "doublequoted = \"test4 \"\n"
                "integer = 1\n"
                "#comment\n"
                "\n"
                "obj = [1, 2, 3]\n")

        c = config.ConfigFile(f)

        self.assertEquals(c.get("nospace"), "test1")
        self.assertEquals(c.get("space"), "test2")
        self.assertEquals(c.get("quoted"), "test3 ")
        self.assertEquals(c.get("doublequoted"), "test4 ")
        self.assertEquals(c.get("integer"), 1)
        self.assertEquals(c.get("obj"), [1, 2, 3])

    def test_ids(self):
        """
        Test that the correct values are pulled depending on the ids passed in
        """

        f = StringIO.StringIO("test=foo\n"
                "%live.test=bar\n"
                "%live01.test=baz\n"
                )

        c = config.ConfigFile(f)

        self.assertEquals(c.get("test"), "foo")
        self.assertEquals(c.get("test", ids=["live"]), "bar")
        self.assertEquals(c.get("test", ids=["live01", "live"]), "baz")
        self.assertEquals(c.get("test", ids=["live02", "live"]), "bar")
        self.assertEquals(c.get("test", ids=["dev01", "dev"]), "foo")

    def test_get_set_id(self):
        oldId = config.get_ids()
        config.set_ids(["live01", "live"])
        newId = config.get_ids()

        self.assertEquals(newId, ["live01", "live"])

        config.set_ids(oldId)

