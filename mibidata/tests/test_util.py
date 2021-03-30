"""Tests for mibidata.util

Copyright (C) 2021 Ionpath, Inc.  All rights reserved."""

import unittest
import numpy as np
from numpy.testing import assert_array_equal

from mibidata import util


class TestUtil(unittest.TestCase):

    def test_natural_sort(self):
        names = ['Image0.msdf', 'Image0.h5', 'Image10.h5', 'Image2.h5']
        util.natural_sort(names)
        expected_names = ['Image0.h5', 'Image0.msdf', 'Image2.h5', 'Image10.h5']
        self.assertEqual(names, expected_names)


    def test_encode_list(self):

        strings = ['Five', 'birds', 'one', 'stone']
        bytes_objects = ['Five'.encode('utf-8'), 'birds'.encode('utf-8'),
                         'one'.encode('utf-8'), 'stone'.encode('utf-8')]

        encoded = util.encode_strings(strings)
        self.assertListEqual(encoded, bytes_objects)


    def test_decode_list(self):

        strings = ['Five', 'birds', 'one', 'stone']
        bytes_objects = ['Five'.encode('utf-8'), 'birds'.encode('utf-8'),
                         'one'.encode('utf-8'), 'stone'.encode('utf-8')]

        decoded = util.decode_strings(bytes_objects)
        self.assertListEqual(decoded, strings)


    def test_sort_channel_names(self):
        expected_list = ["30CD", "35 CD", "CD20", "CD45", "dsDNA", "FOXP3",
                         "HLA DR", "Keratin", "PD-L1", "Vimentin",
                         "\u03D0-tubulin", "23", "150", "151", "162", "165",
                         "175"]

        unsorted_list = ["165", "dsDNA", "23", "Keratin", "CD45", "CD20", "162",
                         "35 CD", "151", "\u03D0-tubulin", "FOXP3", "PD-L1",
                         "175", "30CD", "Vimentin", "HLA DR", "150"]

        util.sort_channel_names(unsorted_list)

        self.assertListEqual(unsorted_list, expected_list)


    def test_format_for_filename(self):

        input_names = ['ChannelWith/Slash', 'ChannelWithoutSlash',
                       'ChannelWithDouble\\Slash', 'NF-\u03BAB']
        expected_names = ['ChannelWith-Slash', 'ChannelWithoutSlash',
                          'ChannelWithDouble-Slash', 'NF-κB']

        formatted_names = [util.format_for_filename(n) for n in input_names]

        self.assertListEqual(formatted_names, expected_names)


    def test_car2pol(self):

        x_c, y_c = 0, 0

        x = np.array([1, 0, -1, 0])
        y = np.array([0, 1, 0, -1])

        expected_r = np.array([1., 1., 1., 1.])
        expected_phi = np.arange(4)*np.pi/2.
        expected_phi_deg = np.arange(4)*90.

        r, phi = util.car2pol(x, y, x_c, y_c)

        assert_array_equal(r, expected_r)
        assert_array_equal(phi, expected_phi)

        phi_deg = util.car2pol(x, y, x_c, y_c, degrees=True)[1]
        assert_array_equal(phi_deg, expected_phi_deg)


if __name__ == '__main__':
    unittest.main()
