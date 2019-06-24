"""Tests for mibitof.panel"""

import os
import shutil
import tempfile
import unittest

import pandas as pd

from mibidata import panels


class TestPanel(unittest.TestCase):

    @classmethod
    def setUp(cls):
        cls.folder = tempfile.mkdtemp()
        cls.filename = os.path.join(cls.folder, 'test.csv')

        cls.simple_csv = 'Mass,Target\n10,Target1\n20,Target2\n30,Target3\n' + \
                         '20,Target4'

        cls.unique_simple_csv = 'Mass,Target\n10,Target1\n20,Target2\n30,' + \
        'Target3'

        cls.tracker_csv = 'Panel ID,0\nPanel Name,The Panel,\nProject ID,0\n' +\
            'Project Name,The Project\nManufacture Data,2018-04-25\n,' +\
            'Description,It has a panel\n\n' +\
            'Batch,0\nTotal Volume (uL),100\nAntibody Volume (uL),5\n' +\
            'Buffer Volume (uL), 105\n\n' +\
            'ID (Lot),Target,Clone,Mass,Element\n' +\
            '001,Target1,A,10,B\n' +\
            '003,Target2,B,20,Ne\n' +\
            '002,Target3,C,30,P\n' + \
            '004,Target4,D,20,Ne'

        cls.tracker_multi_csv = 'Panel ID,0\nPanel Name,The Panel\n' +\
            'Project ID,0\n' +\
            'Project Name,The Project\nManufacture Data,2018-04-25\n' +\
            'Description,It has a panel\n\n' +\
            'Batch,0\nTotal Volume (uL),100\nAntibody Volume (uL),5\n' +\
            'Buffer Volume (uL),105\n\n' +\
            'ID (Lot),Target,Clone,Mass,Element\n' +\
            '001,Target1,A,10,B\n\n' +\
            'Batch,1\nTotal Volume (uL),200\nAntibody Volume (uL),20\n' +\
            'Buffer Volume (uL),220\n\n' +\
            'ID (Lot),Target,Clone,Mass,Element\n' +\
            '003,Target2,B,20,Ne\n' +\
            '002,Target3,C,30,P\n' + \
            '004,Target4,D,20,Ne'

        cls.tracker_multi_csv_with_empty_cells =\
            'Panel ID,0,,,\n' +\
            'Panel Name,The Panel,,,\n' +\
            'Project ID,0,,,\n' +\
            'Project Name,The Project,,,\n' +\
            'Manufacture Data,4/25/2018,,,\n' +\
            'Description,It has a panel,,,\n' +\
            ',,,,\n' +\
            'Batch,0,,,\n' +\
            'Total Volume (uL),100,,,\n' +\
            'Antibody Volume (uL),5,,,\n' +\
            'Buffer Volume (uL),105,,,\n' +\
            ',,,,\n' +\
            'ID (Lot),Target,Clone,Mass,Element\n' +\
            '001,Target1,A,10,B\n' +\
            ',,,,\n' +\
            'Batch,1,,,\n' +\
            'Total Volume (uL),200,,,\n' +\
            'Antibody Volume (uL),20,,,\n' +\
            'Buffer Volume (uL),220,,,\n' +\
            ',,,\n' +\
            'ID (Lot),Target,Clone,Mass,Element\n' +\
            '003,Target2,B,20,Ne\n' +\
            '002,Target3,C,30,P\n' +\
            '004,Target4,D,20,Ne'

        cls.forwards_merge_csv = 'Mass,Target\n10,Target1\n20,Target2\n' + \
                         '30,Target3\n10,Target4\n30,Target5\n10,Target6\n' + \
                         '30,Target7'

        cls.backwards_merge_csv = 'Mass,Target\n30,Target7\n10,Target6\n' + \
                         '30,Target5\n10,Target4\n30,Target3\n20,Target2\n' + \
                         '10,Target1'

        cls.expected_df = pd.DataFrame(
            {'Mass': [10, 20, 30],
             'Target': ['Target1', 'Target2, Target4', 'Target3']},
            columns=['Mass', 'Target'])

        cls.unique_expected_df = pd.DataFrame(
            {'Mass': [10, 20, 30],
             'Target': ['Target1', 'Target2', 'Target3']},
            columns=['Mass', 'Target'])

        cls.expected_merged_df = pd.DataFrame(
            {'Mass': [10, 20, 30],
             'Target': ['Target1, Target4, Target6', 'Target2', 'Target3,' + \
             ' Target5, Target7']},
            columns=['Mass', 'Target'])

        cls.expected_merged_reverse_df = pd.DataFrame(
            {'Mass': [30, 10, 20],
             'Target': ['Target3, Target5, Target7', 'Target1, Target4,' + \
             ' Target6', 'Target2']},
            columns=['Mass', 'Target'])

    @classmethod
    def tearDown(cls):
        shutil.rmtree(cls.folder)

    @classmethod
    def write_csv_string(cls, csv_string):
        """Writes the specified csv_string to the test file defined in setUp()

        Args:
            csv_string: CSV formatted string to write to a temp file.
        """

        with open(cls.filename, 'wt') as f:
            f.write(csv_string)

    def test_read_simple_panel(self):
        self.write_csv_string(self.simple_csv)

        loaded = panels.read_csv(self.filename)

        pd.testing.assert_frame_equal(loaded, self.expected_df)

    def test_read_unique_simple_panel(self):
        self.write_csv_string(self.unique_simple_csv)

        loaded = panels.read_csv(self.filename)

        pd.testing.assert_frame_equal(loaded, self.unique_expected_df)

    def test_read_tracker_panel(self):
        self.write_csv_string(self.tracker_csv)

        loaded = panels.read_csv(self.filename)

        pd.testing.assert_frame_equal(loaded, self.expected_df)

    def test_read_tracker_panel_with_two_batches(self):
        self.write_csv_string(self.tracker_multi_csv)

        loaded = panels.read_csv(self.filename)

        pd.testing.assert_frame_equal(loaded, self.expected_df)

    def test_read_tracker_panel_with_empty_cells(self):
        self.write_csv_string(self.tracker_multi_csv_with_empty_cells)

        loaded = panels.read_csv(self.filename)

        pd.testing.assert_frame_equal(loaded, self.expected_df)

    def test_merge_panels_with_repeated_masses(self):
        self.write_csv_string(self.forwards_merge_csv)

        loaded = panels.read_csv(self.filename)

        pd.testing.assert_frame_equal(loaded, self.expected_merged_df)

    def test_merge_panels_with_repeated_masses_reverse(self):
        self.write_csv_string(self.backwards_merge_csv)

        loaded = panels.read_csv(self.filename)

        pd.testing.assert_frame_equal(loaded, self.expected_merged_reverse_df)

if __name__ == '__main__':
    unittest.main()
