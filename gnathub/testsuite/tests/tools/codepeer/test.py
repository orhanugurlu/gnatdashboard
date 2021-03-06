"""Check that all files have been created."""

import os
import os.path

from ConfigParser import SafeConfigParser

from unittest import TestCase
from support.mock import GNAThub, Project, Script

import csv
from collections import defaultdict

RESULTS = sorted([
    'f.adb',
    'f.adb 18:32',
    'f.ads',
    'simple.adb',
    'simple.adb 30:24',
    'simple.adb 37:8'
])

# For .csv content check
EXPECTED_LINES_FROM_CSV = ['18', '30', '37']
EXPECTED_COLUMNS_FROM_CSV = ['32', '24', '8']
EXPECTED_CATEGORIES_FROM_CSV = [
    'validity check',
    'test always true',
    'dead code']
EXPECTED_RANKINGS_FROM_CSV = ['high', 'medium', 'medium']
EXPECTED_KINDS_FROM_CSV = ['check', 'warning', 'warning']
EXPECTED_MESSAGES_FROM_CSV = [
    'validity check: uninitialized is uninitialized here',
    'test always true because J <= (42) - 38',
    'dead code because (1) = (42) - 41']

class TestCodePeerSupport(TestCase):
    def setUp(self):
        self.longMessage = True

    def testDatabaseContent(self):
        PROJECT = Project.simple()

        # Create path to /obj and /codepeer folders
        OBJ_FOLDER = 'obj'
        OBJ_PATH = os.path.join(Project.simple().install_dir, OBJ_FOLDER)

        CODEPEER_FOLDER = 'codepeer'
        CODEPEER_PATH = os.path.join(OBJ_PATH, CODEPEER_FOLDER)

        # Run GNAThub with Codepeer
        gnathub = GNAThub(PROJECT, plugins=['codepeer'])

        # Check that /obj and /codepeer folders exists
        assert os.path.exists(OBJ_PATH), 'Object folder should exist'
        assert os.path.exists(CODEPEER_PATH), 'Codepeer folder should exist'

        # Check the existence of expected simple.csv file
        CSV_COUNT = 0
        CSV_PATH = CODEPEER_PATH
        for entry in os.listdir(CODEPEER_PATH):
            if entry.endswith('.csv') and entry.startswith('simple'):
                CSV_COUNT += 1
                CSV_PATH = os.path.join(CSV_PATH, entry)
        assert CSV_COUNT == 1, 'simple.csv should be generated in /obj/codepeer folder'
        assert os.path.isfile(CSV_PATH), 'simple.csv is a file'

        # Check .csv content
        columns = defaultdict(list) # each value in each column is appended to a list
        with open(CSV_PATH) as f:
            # read rows into a dictionary format
            reader = csv.DictReader(f)
            # read a row as {column1: value1, column2: value2,...}
            for row in reader:
                # go over each column name and value
                for (k,v) in row.items():
                    # append the value into the appropriate list based on column name k
                    columns[k].append(v)

        # Check column 'Line'
        self.assertListEqual(columns['Line'], EXPECTED_LINES_FROM_CSV)
        # Check column 'Column'
        self.assertListEqual(columns['Column'], EXPECTED_COLUMNS_FROM_CSV)
        # Check column 'Category'
        self.assertListEqual(columns['Category'], EXPECTED_CATEGORIES_FROM_CSV)
        # Check column 'Ranking'
        self.assertListEqual(columns['Ranking'], EXPECTED_RANKINGS_FROM_CSV)
        # Check column 'Kind'
        self.assertListEqual(columns['Kind'], EXPECTED_KINDS_FROM_CSV)
        # Check column 'Message'
        self.assertListEqual(columns['Message'], EXPECTED_MESSAGES_FROM_CSV)

        # Checks the analysis report results are as expected
        script_output_file = os.path.abspath('script.out')
        gnathub.run(script=Script.db2cfg(), output=script_output_file)

        parser = SafeConfigParser()
        parser.optionxform = str

        parser.read(script_output_file)
        self.assertListEqual(sorted(parser.sections()), RESULTS)
