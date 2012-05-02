"""
A wrapper for argparse that lets you dynamically specify command line commands
that have their own arguments that can be parsed
"""

import argparse
import sys

commands = {}

def command(fn):
    """
    A decorator that adds this function as an first level command
    """
    commands[fn.__name__.lower()] = fn
    return fn

@command
def help(args, description):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('command', help="The command to run",
            choices=commands.keys())

    if not args:
        parser.print_help()
    elif args[0] in commands:
        a = ["-h"]
        c = "%s %s" % (sys.argv[0], args[0])
        parser = argparse.ArgumentParser(prog=c, description=description)
        commands[args[0]](a, parser)
    else:
        parser.parse_args(args)
    
def parse(args, description):
    if args and args[0] in commands:
        if args[0] == "help":
            return help(args[1:], description)
        else:
            parser = argparse.ArgumentParser(prog="%s %s" % (sys.argv[0],
                args[0]), description=description)
            commands[args[0]](args[1:], parser)
    else:
        help(args, description)
