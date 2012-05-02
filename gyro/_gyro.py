"""
The command line client for Gyro
"""
import sys
from gyro import util, runner
from gyro.command import command, parse

@command
def new(args, parser):
    parser.description = "Create a new Gyro project"
    parser.add_argument("name", help="the name of your new project")
    parser.add_argument("--path", dest="path", default=None, 
            help="the path in which to create the project")
    a = parser.parse_args(args)

    util.createNewProject(**a.__dict__)

@command
def dev(args, parser):
    parser.description = "Run a Gyro project in development mode"
    parser.add_argument("--path", dest="path", default=None,
            help="the path of the project you want to run (optional)")
    a = parser.parse_args(args)
    a.development = True

    runner.run(**a.__dict__)

def run():
    parse(sys.argv[1:], "Gyro web server")

if __name__ == "__main__":
    run()
