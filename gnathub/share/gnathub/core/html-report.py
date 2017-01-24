# GNAThub (GNATdashboard)
# Copyright (C) 2016-2017, AdaCore
#
# This is free software;  you can redistribute it  and/or modify it  under
# terms of the  GNU General Public License as published  by the Free Soft-
# ware  Foundation;  either version 3,  or (at your option) any later ver-
# sion.  This software is distributed in the hope  that it will be useful,
# but WITHOUT ANY WARRANTY;  without even the implied warranty of MERCHAN-
# TABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public
# License for  more details.  You should have  received  a copy of the GNU
# General  Public  License  distributed  with  this  software;   see  file
# COPYING3.  If not, go to http://www.gnu.org/licenses for a complete copy
# of the license.

"""GNAThub plug-in for the generation of a standalone rich HTML report.

It exports the HTMLReport class which implements the :class:`GNAThub.Plugin`
interface. This allows GNAThub's plug-in scanner to automatically find this
module and load it as part of the GNAThub default execution.
"""

import GNAThub

import json
import inspect
import os

from GNAThub import Console, Plugin, Reporter

from shutil import copy2, copytree, rmtree
from _report import ReportBuilder


class HTMLReport(Plugin, Reporter):
    """HTMLReport plugin for GNAThub."""

    def __init__(self):
        super(HTMLReport, self).__init__()
        self._report = None

    @property
    def name(self):
        return 'html-report'

    @property
    def webapp_dir(self):
        """Return the path to the webapp directory.

        This directory contains the generic parts of the web application.

        :rtype: str
        """
        this = inspect.getfile(inspect.currentframe())
        return os.path.join(os.path.dirname(os.path.dirname(this)), 'webui')

    def setup(self):
        """Inherited."""
        super(HTMLReport, self).setup()
        self._report = ReportBuilder()

    @property
    def output_dir(self):
        """Return the path to the directory where to generate the HTML report.

        :return: the full path to the output directory
        :rtype: str
        """

        return os.path.join(GNAThub.root(), self.name)

    def _write_json(self, output, obj, **kwargs):
        """Dump a JSON-encoded representation of `obj` into `output`.

        :param str output: path to the output file
        :param obj: object to serialize and save into `output`
        :type obj: dict or list or str or int
        :param dict kwargs: the parameters to pass to the underlying
            :func:`json.dumps` function; see :func:`json.dumps` documentation
            for more information
        :raises: IOError
        :see: :func:`json.dumps`
        """

        self.log.debug('generating %s', output)
        with open(output, 'w') as outfile:
            outfile.write(json.dumps(obj, **kwargs))

    def report(self):
        """Generate JSON-encoded representation of the data collected."""

        # The output directory for the JSON-encoded report data
        data_output_dir = os.path.join(self.output_dir, 'data')
        data_src_output_dir = os.path.join(data_output_dir, 'src')

        def _write_report_src_hunk(project, source_dir, source):
            """Write a report source hunk to disk.

            :param str project: the name of the project
            :param str source_dir: the source directory in which to find the
                source
            :param dict[str, *] source: the source metadata (as generated by
                the method :meth:`_generate_report_index`)
            """

            def _fname(ext):
                return '{}.{}'.format(os.path.join(
                    data_src_output_dir, source['filename']), ext)

            self.log.debug('processing %s', source['filename'])
            src_hunk = self._report.generate_src_hunk(
                project, source_dir, source['filename'])
            self._write_json(_fname('json'), src_hunk, indent=2)
            self.log.debug('src hunk written to %s', _fname('json'))

        def _write_report_index(project_name, index):
            """Write the report index to disk.

            :param str project_name: the name of the project
            """

            def _fname(ext):
                return os.path.join(data_output_dir, 'report.{}'.format(ext))

            self._write_json(_fname('json'), index, indent=2)
            self.log.debug('report index written to %s', _fname('json'))

        try:
            self.info('generate JSON-encoded report')

            # Create directory structure if needed
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)
            else:
                self.log.warn('%s: already exists', self.output_dir)
                self.log.warn('existing report may be overriden')

            # Copy the generic web application files
            for entry in os.listdir(self.webapp_dir):
                path = os.path.join(self.webapp_dir, entry)
                dest = os.path.join(self.output_dir, entry)
                if os.path.isdir(path):
                    if os.path.isdir(dest):
                        rmtree(dest)
                    copytree(path, dest)
                else:
                    copy2(path, dest)

            # Create the JSON-encoded report output directory
            for directory in (data_output_dir, data_src_output_dir):
                if not os.path.exists(directory):
                    os.makedirs(directory)

            # Generate the report index
            report_index = self._report.generate_index()

            # Compute the total source file count to display execution progress
            # Note: this is a more efficient version of:
            #
            #   count, total = 0, 1
            #   for source_dirs in report_index['modules'].values():
            #       for source_hunks in source_dirs.values():
            #           total += len(source_hunks)
            #
            # Using generators and the built-in sum function, the following
            # code ensures the smaller memory footprint and the best
            # opportunities for the Python VM to optimize the count
            # computation.
            count, total = 0, sum((sum((
                len(source_dir['sources'])
                for source_dir in module['source_dirs'].itervalues()
            )) for module in report_index['modules'].itervalues())) + 1

            # Serialize each source of the project
            for project, module in report_index['modules'].iteritems():
                for dirname, source_dir in module['source_dirs'].iteritems():
                    for src_hunk in source_dir['sources']:
                        _write_report_src_hunk(project, dirname, src_hunk)
                        count = count + 1
                        assert count != total, 'internal error'
                        Console.progress(count, total, False)

            # Serialize the index
            _write_report_index(GNAThub.Project.name(), report_index)
            assert count + 1 == total, 'internal error'
            Console.progress(count + 1, total, True)
            self.info('report written to %s', self.output_dir)

        except IOError as why:
            self.log.exception('failed to generate the HTML report')
            self.error(str(why))
            return GNAThub.EXEC_FAILURE

        else:
            return GNAThub.EXEC_SUCCESS
