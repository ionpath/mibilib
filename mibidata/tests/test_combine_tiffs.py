"""Tests for mibidata.combine_tiffs

Copyright (C) 2019 Ionpath, Inc.  All rights reserved.
"""

import unittest

from mibidata import combine_tiffs


class TestRuns(unittest.TestCase):

    def test_match_target_filename(self):
        filenames = ['CD45.tif', 'CD8.tiff', 'dsDNA.png', 'FoxP3.TIFF']
        self.assertEqual(
            combine_tiffs._match_target_filename(filenames, 'CD45'),
            'CD45.tif'
        )
        self.assertEqual(
            combine_tiffs._match_target_filename(filenames, 'CD8'),
            'CD8.tiff'
        )
        self.assertEqual(
            combine_tiffs._match_target_filename(filenames, 'FoxP3'),
            'FoxP3.TIFF'
        )
        with self.assertRaises(ValueError):
            combine_tiffs._match_target_filename(filenames, 'dsDNA')


if __name__ == '__main__':
    unittest.main()
