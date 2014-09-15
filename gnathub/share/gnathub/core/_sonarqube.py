############################################################################
#                                                                          #
#                               G N A T h u b                              #
#                                                                          #
#                     Copyright (C) 2013-2014, AdaCore                     #
#                                                                          #
# This is free software;  you can redistribute it  and/or modify it  under #
# terms of the  GNU General Public License as published  by the Free Soft- #
# ware  Foundation;  either version 3,  or (at your option) any later ver- #
# sion.  This software is distributed in the hope  that it will be useful, #
# but WITHOUT ANY WARRANTY;  without even the implied warranty of MERCHAN- #
# TABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public #
# License for  more details.  You should have  received  a copy of the GNU #
# General  Public  License  distributed  with  this  software;   see  file #
# COPYING3.  If not, go to http://www.gnu.org/licenses for a complete copy #
# of the license.                                                          #
#                                                                          #
############################################################################

"""Helper module to factorize shared components between SonarConfig and
SonarRunner.
"""

import collections
import logging
import os
import shutil

import GNAThub
from GNAThub import Console


class SonarQube(object):
    """Provides a set of helper static methods used by both the SonarQube
    Runner plug-in and the SonarConfig plug-in.

    """

    EXEC_DIRECTORY = 'sonar'
    CONFIGURATION = 'sonar-project.properties'

    SOURCE_CACHE = 'sources.cache'
    SOURCE_MAPPING = 'sources-mapping.properties'

    @staticmethod
    def workdir():
        """Returns the sonar execution directory located within GNAThub's root
        directory:

            ``<project_object_dir>/gnathub/sonar``

        :return: The path to the working directory.
        :rtype: str

        """

        return os.path.join(GNAThub.root(), SonarQube.EXEC_DIRECTORY)

    @staticmethod
    def configuration():
        """Returns the path to the SonarQube Runner configuration file located
        in the Sonar-specific directory:

            ``<project_object_dir>/gnathub/sonar/sonar-project.properties``

        :return: The path to the configuration file.
        :rtype: str

        """

        return os.path.join(SonarQube.workdir(), SonarQube.CONFIGURATION)

    @staticmethod
    def src_mapping():
        """Returns the path to the mapping file associating original sources
        path with the equivalent source in the local cache:

            ``<project_object_dir>/gnathub/sonar/sources.map``

        :return: The path to the configuration file.
        :rtype: str

        """

        return os.path.join(SonarQube.workdir(), SonarQube.SOURCE_MAPPING)

    @staticmethod
    def src_cache():
        """Returns the path to the local source cache containing a copy of all
        analysed sources:

            ``<project_object_dir>/gnathub/sonar/sources.cache``

        :return: The path to the source cache.
        :rtype: str

        """

        return os.path.join(SonarQube.workdir(), SonarQube.SOURCE_CACHE)

    @staticmethod
    def make_workdir():
        """Creates the Sonar execution directory if it does not exist."""

        if not os.path.exists(SonarQube.workdir()):
            os.makedirs(SonarQube.workdir())


# pylint: disable=too-few-public-methods
class SonarRunnerProperties(object):
    """Builder object for the sonar-runner configuration file."""

    CONSOLE_NAME = 'sonar-gen-config'

    def __init__(self, logger=None):
        self.log = logger or logging.getLogger(self.__class__.__name__)

        self.attributes = collections.OrderedDict()
        self.src_mapping = collections.OrderedDict()

        # Generate the configuration
        self._generate()

    def info(self, message):
        """Displays an informative message.

        :param str message: The message to display.

        """

        # pylint: disable=no-self-use
        Console.info(message, prefix=SonarRunnerProperties.CONSOLE_NAME)

    def error(self, message):
        """Displays an error message.

        :param str message: The message to display.

        """

        # pylint: disable=no-self-use
        Console.error(message, prefix=SonarRunnerProperties.CONSOLE_NAME)

    @staticmethod
    def _key(key, module=None):
        """Generates the full key.

        :param str key: Property key.
        :param str module: Module to which belongs the key. If ``None``, use
            the default sonar module.
        :return: The key.
        :rtype: str

        """

        return '%s.%s' % ('%s.sonar' % module if module else 'sonar', key)

    def _set(self, key, value, module=None):
        """Adds property in the sonar-runner configuration.

        :param str key: Property key.
        :param str value: Property value.
        :param str module: Module to which belongs the key. If ``None``, use
            the default sonar module.

        """

        self.attributes[SonarRunnerProperties._key(key, module)] = value

    def _set_dict(self, attributes, module=None):
        """Adds properties in the sonar-runner configuration.

        :param dict[str, str] attributes: Attributes to set.
        :param str module: Module to which belongs the key. If ``None``, use
            the default sonar module.

        """

        for key, value in attributes.items():
            self.log.debug('%s = %s', key, value)
            self._set(key, value, module)

    def _set_project_customizable_dict(self, attributes, module=None):
        """Adds properties in the sonar-runner configuration.

        Those properties can be user-customizable via the project file.

        :param dict[str, (str, str)] attributes: Attributes to set.
        :param str module: Module to which belongs the key. If ``None``, use
            the default sonar module.

        """

        for key, value in attributes.items():
            # Unpack the tuple containing the default value and the custom
            # project attribute for this key.
            value, attribute = value

            assert attribute, 'use SonarRunnerProperties._set_dict instead'
            project_property = GNAThub.Project.property_as_string(attribute)

            if project_property:
                self.log.debug('%s = %s (overriding default)', key, value)
            else:
                self.log.debug('%s = %s', key, value)

            self._set(key, project_property or value, module)

    def _get(self, key, module=None):
        """Returns the property in the sonar-runner configuration.

        :param str key: Property key.
        :param str module: Module to which belongs the key. If ``None``, use
            the default sonar module.
        :return: The value of the property ``key``.
        :rtype: str

        """

        return self.attributes.get(SonarRunnerProperties._key(key, module))

    def _generate(self):
        """Generates the content of the sonar-runner.properties file.

        Do not create the file yet. See :meth:`write` for this.

        """

        kwargs = {
            'db_path': GNAThub.database().replace('\\', '\\\\'),
            'project_name': GNAThub.Project.name(),
            'suffixes': [s[1:] if s.startswith('.') else s
                         for s in GNAThub.Project.source_suffixes('Ada')]
        }

        # pylint: disable=star-args
        if len(GNAThub.Project.source_dirs()) == 1:
            self._generate_single_module(**kwargs)
        else:
            self._generate_multi_module(**kwargs)

    @staticmethod
    def _generate_customizable_attr(project_name):
        """A dictionary of customizable attributes for the
        :file:`sonar-project.properties`.

        :param str project_name: The project name.
        :return: The attributes and their value.
        :rtype: collections.OrderedDict

        """

        return collections.OrderedDict([
            ('projectName', (project_name, 'Project_Name')),
            ('projectKey', (project_name, 'Project_Key')),
            ('projectVersion', ('unknown', 'Project_Version')),
            ('sourceEncoding', ('UTF-8', 'Source_Encoding'))
        ])

    def _generate_single_module(self, db_path, project_name, suffixes):
        """Generates the content of the sonar-runner.properties file.

        Do not create the file yet. See :meth:`write` for this.

        :param str db_path: Full path to the DB.
        :param str project_name: Project name.
        :param list[str] suffixes: List of Ada extensions.

        """

        source_dirs = GNAThub.Project.source_dirs()[project_name]
        sources, _ = self._generate_source_dirs({project_name: source_dirs})

        non_customizable_attributes = collections.OrderedDict([
            ('language', 'ada'),
            ('sources', sources),
            ('ada.gnathub.db', db_path),
            ('ada.file.suffixes', ','.join(suffixes))
        ])

        # Set project properties
        self._set_project_customizable_dict(
            SonarRunnerProperties._generate_customizable_attr(project_name))
        self._set_dict(non_customizable_attributes)

    def _generate_multi_module(self, db_path, project_name, suffixes):
        """Generates the content of the sonar-runner.properties file.

        Do not create the file yet. See :meth:`write` for this.

        :param str db_path: Full path to the DB.
        :param str project_name: Project name.
        :param list[str] suffixes: List of Ada extensions.

        """

        modules = {k: v for k, v in GNAThub.Project.source_dirs().items() if v}
        _, modules = self._generate_source_dirs(modules)

        non_customizable_attributes = collections.OrderedDict([
            ('language', 'ada'),
            ('ada.gnathub.db', db_path),
            ('ada.gnathub.src_mapping', SonarQube.src_mapping()),
            ('ada.file.suffixes', ','.join(suffixes)),
            ('modules', ','.join([m.lower() for m in modules.keys()]))
        ])

        # Set project properties
        self._set_project_customizable_dict(
            SonarRunnerProperties._generate_customizable_attr(project_name))
        self._set_dict(non_customizable_attributes)

        project_key = self._get('projectKey')

        # Set modules properties
        for subproject_name, sources in modules.items():
            module_attributes = collections.OrderedDict([
                ('projectName', subproject_name),
                ('projectKey', '%s::%s' % (project_key, subproject_name)),
                ('projectBaseDir', SonarQube.src_cache()),
                ('sources', sources)
            ])

            self._set_dict(module_attributes, module=subproject_name.lower())

    # pylint: disable=too-many-locals
    def _generate_source_dirs(self, modules):
        """Copy over all sources in a temporary directory before running the
        Sonar Runner. This is to work around recent version of SonarQube source
        importer implementation that looks recursively in source directories
        (which is inconsistent with GPR files semantic).

        :param dict[str,list[str]] modules: Project modules and their
            associated source directories.
        :return: The path to the root source directory and a copy of the input
            ``modules`` directory with updated path to source directories
            (pointing to the local copy).
        :rtype: (str, dict[str,list[str]])

        """

        self.log.debug('caching source dirs prior to sonar-runner execution')

        # Compute the total dirs count to copy to display progress
        count = 0
        total = sum([len(dirs) for dirs in modules.itervalues()])

        root_src_dir = SonarQube.src_cache()

        self.info('prepare source dirs for sonar-runner scan')
        self.log.info('copy source files from the project closure to %s' %
                      os.path.relpath(root_src_dir))

        # Remove any previous analysis left-over
        shutil.rmtree(root_src_dir, ignore_errors=True)
        new_modules_mapping = collections.OrderedDict()

        for module_name in modules:
            module_root_src_dir = os.path.join(root_src_dir, module_name)
            new_modules_mapping[module_name] = module_root_src_dir

            # Add an additional subdirectory.
            # NOTE: SonarQube uses "[root]" as the root directory name, which
            # means that when we have a flat list of source files, they all end
            # up in different "[root]" dirs in SonarQube UI.  Since each
            # project can have a "[root]" directory, it makes it harder to read
            # the hierarchy.  To work around that, we interpose an additional
            # "<module-name>-src" directory to make things clearer from a UI
            # point of view.
            module_root_src_dir = os.path.join(module_root_src_dir,
                                               module_name.lower() + '-src')

            # Create the local source directory
            if not os.path.exists(module_root_src_dir):
                os.makedirs(module_root_src_dir)

            # Compute the base directory for source dirs.
            # NOTE: The GNAT Project language allows the user to specify a list
            # of source directories that are not necessarily all under the same
            # hierarchy. Furthermore, and this is the default behavior, it
            # allows the user to specify non-recursive source directories:
            # source directories which contain sub-directories which are not
            # themselves source directories. The SonarQube model requires all
            # sources in specified source directories to be in the source
            # closure: to satisfy this requirement, we gather all sources under
            # a same tree, and do a best effort to mimic the original
            # organization of sources.
            module_src_dirs = modules[module_name]
            dirs_commonprefix = os.path.commonprefix(module_src_dirs)
            self.log.info('source dirs common prefix: %s', dirs_commonprefix)

            # Use a dict to ensure we don't have duplicated names
            src_files = {}

            # Copy each source dir content
            self.info('prepare files from module: %s' % module_name)
            for src_dir in modules[module_name]:
                src_dir_relpath = os.path.relpath(src_dir, dirs_commonprefix)
                src_dir_path = os.path.join(module_root_src_dir,
                                            src_dir_relpath)
                self.log.info(' + %s' % src_dir_path)

                if not os.path.exists(src_dir_path):
                    os.makedirs(src_dir_path)

                # Copy over all files
                for entry in os.listdir(src_dir):
                    entry_path = os.path.join(src_dir, entry)

                    if not os.path.isfile(entry_path):
                        continue

                    if entry in src_files:
                        self.error('duplicated source file: %s' % entry)
                        self.error('  + %s' % src_files[entry])
                        self.error('  + %s' % entry_path)

                    src_files[entry] = entry_path

                    new_path = os.path.join(src_dir_path, entry)
                    self.log.debug('%s -> %s', entry_path, new_path)

                    shutil.copy(entry_path, new_path)
                    self.src_mapping[entry_path] = new_path

                count = count + 1
                Console.progress(count, total, count == total)

        return root_src_dir, new_modules_mapping

    def write(self, properties_fname=SonarQube.configuration()):
        """Dumps the Sonar Runner configuration files:

            * :file:`sonar-project.properties` -> ``properties_fname``
            * :file:`sources.map` -> ``SonarQube.src_mapping()``

        :param str properties_fname: The configuration file name.

        """

        def _escape(key):
            """Escapes the given key to comply with java.util.Properties parser
            (see the ``java.util.Properties.load`` method documentation).

            :param str key: The key to escape.
            :return: The escaped key.
            :rtype: str
            :see: docs.oracle.com/javase/8/docs/api/java/util/Properties.html

            """

            escaped = key
            for sym in (':', '=', ' '):
                escaped = escaped.replace(sym, r'\%s' % sym)
            return escaped

        self.info('generate %s' % os.path.relpath(properties_fname))
        with open(properties_fname, 'w') as configuration:
            for pair in self.attributes.items():
                configuration.write('%s = %s\n' % pair)

        self.info('generate %s' % os.path.relpath(SonarQube.src_mapping()))
        with open(SonarQube.src_mapping(), 'w') as mapping:
            for key, value in self.src_mapping.items():
                mapping.write('%s = %s\n' % (_escape(key), value))
