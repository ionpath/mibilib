"""Tests for pseudodepths.py

Copyright (C) 2021 Ionpath, Inc.  All rights reserved."""

import os
import struct
import shutil
import tempfile
import unittest

import numpy as np

from mibidata import pseudodepths

# File variant 1, 8 bins per spectrum, 16 = 4x4 pixels.
NUM_PIXELS = 4
HEADER = (1, 8, NUM_PIXELS)
# Assume 10 cycles per pixel, so each data sub-list has 10 zeros and the rest
# of the counts are bin numbers from 1 to 8. The (0, 0) entry to indicate
# new cycle comes at the _end_ of the data for each cycle.
#
# This following data was generated with:
#
# pixel_lengths = np.random.randint(9, 20, 16)
# DATA = []
# for pl in pixel_lengths:
#     entries = np.zeros(pl, np.int)
#     num_counts = pl - 9
#     inds = np.random.choice(np.arange(pl), num_counts, replace=False)
#     bins = np.random.randint(1, 8, num_counts)
#     entries[inds] = bins
#     DATA.append(list(entries) + [0])
DATA = [
    [0, 3, 0, 1, 1, 0, 3, 0, 0, 0, 3, 0, 3, 7, 3, 4, 0, 0, 5, 0],
    [0, 5, 4, 2, 0, 0, 0, 0, 0, 0, 3, 0, 2, 2, 0, 2, 0],
    [0, 0, 0, 6, 7, 0, 0, 0, 0, 0, 0, 2, 2, 0],
    [0, 1, 1, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0],
]
# How many counts to expect if we manually split into two depths.
DEPTH0 = [
    [0, 3, 0, 1, 1, 0, 3, 0, 0],
    [0, 5, 4, 2, 0, 0, 0, 0],
    [0, 0, 0, 6, 7, 0, 0],
    [0, 1, 1, 0, 0, 3, 0, 0],
]
DEPTH1 = [
    [0, 3, 0, 3, 7, 3, 4, 0, 0, 5, 0],
    [0, 0, 3, 0, 2, 2, 0, 2, 0],
    [0, 0, 0, 0, 2, 2, 0],
    [0, 0, 0, 0, 0],
]


class TestMsdf(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        fh, fn = tempfile.mkstemp()
        cls.msdf = fn
        os.close(fh)
        sat = np.zeros((NUM_PIXELS, 2), np.int)
        cls.header = struct.pack(pseudodepths.HEADER_FORMAT, 1, 8, NUM_PIXELS)
        with open(fn, 'wb') as infile:
            infile.write(cls.header)
            end_sat = pseudodepths.HEADER_SIZE + \
                NUM_PIXELS * pseudodepths.SAT_ENTRY_SIZE
            infile.seek(end_sat)
            for i, pixel in enumerate(DATA):
                sat[i, 0] = infile.tell()
                sat[i, 1] = len(pixel)
                for timestamp in pixel:
                    count = int(timestamp > 0)
                    infile.write(
                        struct.pack(pseudodepths.DATA_FORMAT, timestamp, count))
            infile.seek(pseudodepths.HEADER_SIZE)
            for offset, length in sat:
                infile.write(
                    struct.pack(pseudodepths.SAT_ENTRY_FORMAT, offset, length))
        cls.data_start = end_sat

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls):
        os.remove(cls.msdf)

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def _pack_sat(self, depth):
        sat = b''
        offset = self.data_start
        for d in depth:
            sat += struct.pack(
                pseudodepths.SAT_ENTRY_FORMAT, offset, len(d))
            offset += pseudodepths.DATA_SIZE * len(d)
        return sat

    def _pack_data(self, depth):
        data = b''
        for pixel in depth:
            for i in pixel:
                data += struct.pack(
                    pseudodepths.DATA_FORMAT, i, int(i > 0))
        return data

    def test_split_into_one(self):
        """If we split into one output file, we should get the same file out.
        """
        cycles_per_pixel, cycles_per_scan = pseudodepths.divide(
            self.msdf, 1, self.tempdir)
        self.assertEqual(cycles_per_pixel, 10)
        self.assertEqual(cycles_per_scan, 10)
        new_file = os.path.join(self.tempdir, 'Depth0', 'Image.msdf')
        self.assertTrue(os.path.exists(new_file))
        with open(self.msdf, 'rb') as infile:
            expected_buffer = infile.read()
        with open(new_file, 'rb') as infile:
            new_buffer = infile.read()
        self.assertEqual(new_buffer, expected_buffer)

    def test_split_into_two(self):
        cycles_per_pixel, cycles_per_scan = pseudodepths.divide(
            self.msdf, 2, self.tempdir)
        self.assertEqual(cycles_per_pixel, 10)
        self.assertEqual(cycles_per_scan, 5)
        depth0 = os.path.join(self.tempdir, 'Depth0', 'Image.msdf')
        depth1 = os.path.join(self.tempdir, 'Depth1', 'Image.msdf')
        with open(depth0, 'rb') as infile:
            depth0_header = infile.read(pseudodepths.HEADER_SIZE)
            depth0_sat = infile.read(NUM_PIXELS * pseudodepths.SAT_ENTRY_SIZE)
            depth0_data = infile.read()
        with open(depth1, 'rb') as infile:
            depth1_header = infile.read(pseudodepths.HEADER_SIZE)
            depth1_sat = infile.read(NUM_PIXELS * pseudodepths.SAT_ENTRY_SIZE)
            depth1_data = infile.read()

        self.assertEqual(depth0_header, self.header)
        self.assertEqual(depth1_header, self.header)
        self.assertEqual(depth0_sat, self._pack_sat(DEPTH0))
        self.assertEqual(depth1_sat, self._pack_sat(DEPTH1))
        self.assertEqual(depth0_data, self._pack_data(DEPTH0))
        self.assertEqual(depth1_data, self._pack_data(DEPTH1))

    def test_split_into_three(self):
        """This should raise because the number of cycles is not divisible by
        the number of desired pseudo-depths."""
        with self.assertRaises(ValueError):
            pseudodepths.divide(self.msdf, 3, self.tempdir)

if __name__ == '__main__':
    unittest.main()
