##############################################################################
##                                                                          ##
##                               G N A T h u b                              ##
##                                                                          ##
##                     Copyright (C) 2013-2014, AdaCore                     ##
##                                                                          ##
## The QM is free software; you can redistribute it  and/or modify it       ##
## under terms of the GNU General Public License as published by the Free   ##
## Software Foundation; either version 3, or (at your option) any later     ##
## version.  The QM is distributed in the hope that it will be useful,      ##
## but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHAN-  ##
## TABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public ##
## License  for more details. You  should  have  received a copy of the GNU ##
## General Public License  distributed with the QM; see file COPYING3. If   ##
## not, write  to  the Free  Software  Foundation,  59 Temple Place - Suite ##
## 330, Boston, MA 02111-1307, USA.                                         ##
##                                                                          ##
##############################################################################

"""GNAThub plug-in for the Gcov command-line tool.

It exports the Gcov Python class which implements the GNAThub.Plugin interface.
This allows GNAThub's plug-in scanner to automatically find this module and
load it as part of the GNAThub default execution.
"""

import os

import GNAThub
from GNAThub import Console


# pylint: disable=too-few-public-methods
class Gcov(GNAThub.Plugin):
    """Gcov plugin for GNAThub.

    Retrieves .gcov generated files from teh project root object directory,
    parses them and feeds the database with the data collected from each files.

    """

    GCOV_EXT = '.gcov'

    def __init__(self):
        super(Gcov, self).__init__()

        self.tool = None
        self.rule = None

        # A dictionary containing all messages, to allow bulk insertion in the
        # database: key is an string representing the number of hits,
        # value is the corresponding Message instance.
        self.hits = {}

    def __process_file(self, resource, filename):
        """Processes one file, adding in bulk all coverage info found.

        :param GNAThub.Resource resource: The resource being processed.
        :param str filename: The name of the resource.

        """

        message_data = []

        with open(filename, 'r') as gcov_file:
            # Retrieve information for every source line.
            # Skip the first 2 lines.
            for line in gcov_file.readlines()[2:]:

                # Skip lines that do not contain coverage info
                if line.strip()[0] != '-':
                    line_info = line.split(':', 2)
                    hits = line_info[0].strip()

                    # Line is not covered
                    if hits == '#####' or hits == '=====':
                        hits = '0'

                    line = int(line_info[1].strip())

                    # find the message corresponding to this hits number

                    if hits in self.hits:
                        msg = self.hits[hits]
                    else:
                        msg = GNAThub.Message(self.rule, hits)
                        self.hits[hits] = msg

                    message_data.append([msg, line, 1, 1])

        # We now have a list of messages in message_data: do the bulk insert
        resource.add_messages(message_data)

    def __parse_gcov_report(self):
        """Analyses the report files generated by Gcov.

        Finds all .gcov files in the object directory and parses them.

        Sets the exec_status property according to the success of the
        analysis:

            * ``GNAThub.EXEC_SUCCESS``: on successful execution and analysis
            * ``GNAThub.EXEC_FAILURE``: on any error

        """

        self.info('parse coverage reports (%s)' % self.GCOV_EXT)

        # Fetch all files in project object directory and retrieve only
        # .gcov files, absolute path
        files = [os.path.join(GNAThub.Project.object_dir(), filename)
                 for filename in os.listdir(GNAThub.Project.object_dir())
                 if filename.endswith(self.GCOV_EXT)]

        # If no .gcov file found, plugin returns on failure
        if not files:
            self.error('no %s file in object directory' % self.GCOV_EXT)
            self.exec_status = GNAThub.EXEC_FAILURE
            return

        self.tool = GNAThub.Tool(self.name)
        self.rule = GNAThub.Rule('coverage', 'coverage',
                                 GNAThub.METRIC_KIND, self.tool)

        total = len(files)

        try:
            for index, filename in enumerate(files, start=1):
                # Retrieve source fullname
                base, _ = os.path.splitext(os.path.basename(filename))
                src = GNAThub.Project.source_file(base)

                resource = GNAThub.Resource.get(src)

                if resource:
                    self.__process_file(resource, filename)

                Console.progress(index, total, new_line=(index == total))

        except IOError as why:
            self.exec_status = GNAThub.EXEC_FAILURE
            self.log.exception('failed to parse GCov reports')
            self.error(str(why))

        else:
            self.exec_status = GNAThub.EXEC_SUCCESS

    def execute(self):
        """Finds the Gcov output files and parses them."""

        self.__parse_gcov_report()
