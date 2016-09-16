# -*- coding: utf-8 -*-

""" Main module for sequence execution """

# ------------------------------------------------------------------------------
# Name:        SequenceEngine
# Purpose:     Load and execute sequences from xml files
#
# Author:      michel.vincent
#
# Created:     26/09/2013
# Copyright:   (c) michel.vincent 2013
# Licence:     GPL
# ------------------------------------------------------------------------------

# Imports
import sys
from optparse import OptionParser
from sequence.core.engine import SequenceEngine, stream_sequence_logs


# Command line execution
def main():
    """  Main function for console execution """
    # Parse arguments
    file_name, depth, backup, debug_level = parse_command_line_args()
    # Create Log Handler
    stream_sequence_logs(sys.stdout, debug_level)
    # Load sequence
    engine = SequenceEngine()
    try:
        engine.load(file_name, depth, backup)
    except Exception as exc:
        print(exc)
        return
    # Wait for input
    try:
        res = raw_input("Press 'r' to run, any other key to abort: ")
    except KeyboardInterrupt:
        res = 'a'
    if res.lower() == 'r':
        print("RUN")
        engine.start()
        boolean = False
        while not boolean:
            try:
                boolean = engine.wait(1)
            except KeyboardInterrupt:
                print("USER STOP")
                engine.interrupt()
        print("FINISHED")


# Parse command line
def parse_command_line_args():
    """ Parse arguments given in command line """
    usage = "%prog [options] file_name"
    desc = "Load and run the xml sequence given by the file-name parameter"
    parser = OptionParser(usage=usage, description=desc, version='%prog v1.0')

    msg = "Define the maximum backup depth"
    parser.add_option('-d', '--depth', metavar='DEP',
                      type='int', help=msg)

    msg = "File name of a special backup sequence"
    parser.add_option('-b', '--back', metavar='FILE',
                      type='str', help=msg)

    msg = "Level of the logging messages (from 1 for debug to 5 for critical)"
    parser.add_option('-l', '--log', metavar='LVL',
                      type='int', help=msg, default=2)

    options, args = parser.parse_args()

    if len(args) == 0:
        parser.print_help()
        parser.exit()

    if len(args) > 1:
        parser.error("incorrect number of arguments")

    if options.log not in range(1, 5):
        parser.error("invalid value for logging level")

    res = args[0], options.depth, options.back, options.log*10
    return res


# Main execution
if __name__ == '__main__':
    main()
