"""Tests for mibidata.tiff

Copyright (C) 2019 Ionpath, Inc.  All rights reserved."""

import datetime
import os
import shutil
import tempfile
import unittest
import warnings

import numpy as np
from skimage import io, img_as_ubyte, transform
from skimage.external.tifffile import TiffFile

from mibidata import mibi_image as mi
from mibidata import tiff, util

DATA = np.arange(500).reshape(10, 10, 5).astype(np.uint16)
SED = np.arange(100).reshape(10, 10)
CAROUSEL = np.random.randint(0, 255, (4096, 4096, 3), np.uint8)
X_COORD, Y_COORD = tiff._BOTTOM_LABEL_COORDINATES
LABEL = (img_as_ubyte(transform.rotate(
    CAROUSEL[X_COORD[0]:X_COORD[1], Y_COORD[0]:Y_COORD[1]], 270)))
CHANNELS = ((1, 'Target1'), (2, 'Target2'), (3, 'Target3'),
            (4, 'Target4'), (5, 'Target5'))
METADATA = {
    'run': 'Run', 'date': '2017-09-16T15:26:00',
    'coordinates': (12345, -67890), 'size': 500., 'slide': '857',
    'point_name': 'R1C3_Tonsil', 'dwell': 4, 'scans': '0,5',
    'folder': 'Point1/RowNumber0/Depth_Profile0',
    'aperture': '300um', 'instrument': 'MIBIscope1', 'tissue': 'Tonsil',
    'panel': '20170916_1x', 'mass_offset': 0.1, 'mass_gain': 0.2,
    'time_resolution': 0.5, 'miscalibrated': False, 'check_reg': False,
    'filename': 'Run'
}


class TestTiffHelpers(unittest.TestCase):

    def test_motor_to_cm(self):
        self.assertEqual(tiff._micron_to_cm(10000), (1, 1))

    def test_cm_to_motor(self):
        self.assertEqual(tiff._cm_to_micron((1, 1)), 10000)


class TestWriteReadTiff(unittest.TestCase):

    def setUp(self):
        self.image = mi.MibiImage(DATA, CHANNELS, **METADATA)
        self.folder = tempfile.mkdtemp()
        self.filename = os.path.join(self.folder, 'test.tif')
        self.maxDiff = None

    def tearDown(self):
        shutil.rmtree(self.folder)

    def test_sims_only(self):
        tiff.write(self.filename, self.image)
        image = tiff.read(self.filename)
        self.assertEqual(image, self.image)
        sims, sed, optical, label = tiff.read(self.filename, sed=True,
                                              optical=True, label=True)
        self.assertEqual(sims, self.image)
        self.assertIsNone(sed)
        self.assertIsNone(optical)
        self.assertIsNone(label)
        self.assertEqual(image.data.dtype, np.uint16)

    def test_default_ranges(self):
        tiff.write(self.filename, self.image)
        with TiffFile(self.filename) as tif:
            for i, page in enumerate(tif.pages):
                self.assertEqual(page.tags['smin_sample_value'].value, 0)
                self.assertEqual(page.tags['smax_sample_value'].value,
                                 self.image.data[:, :, i].max())

    def test_custom_ranges(self):
        ranges = list(zip([1]*5, range(2, 7)))
        tiff.write(self.filename, self.image, ranges=ranges)
        with TiffFile(self.filename) as tif:
            for i, page in enumerate(tif.pages):
                self.assertEqual(page.tags['smin_sample_value'].value,
                                 ranges[i][0])
                self.assertEqual(page.tags['smax_sample_value'].value,
                                 ranges[i][1])


    def test_sims_and_sed(self):
        tiff.write(self.filename, self.image, sed=SED)
        image = tiff.read(self.filename)
        self.assertEqual(image, self.image)
        sims, sed, optical, label = tiff.read(self.filename, sed=True,
                                              optical=True, label=True)
        self.assertEqual(sims, self.image)
        np.testing.assert_array_equal(sed, SED)
        self.assertIsNone(optical)
        self.assertIsNone(label)

    def test_sims_and_sed_and_optical_and_label(self):
        tiff.write(self.filename, self.image, sed=SED, optical=CAROUSEL)
        image, sed, optical, label = tiff.read(self.filename, sed=True,
                                               optical=True, label=True)
        self.assertEqual(image, self.image)
        np.testing.assert_array_equal(sed, SED)
        np.testing.assert_array_equal(optical, CAROUSEL)
        np.testing.assert_array_equal(label, LABEL)

    def test_read_sed_only(self):
        tiff.write(self.filename, self.image, sed=SED)
        sed = tiff.read(self.filename, sims=False, sed=True)
        np.testing.assert_array_equal(sed, SED)

    def test_read_optical_and_label_only(self):
        tiff.write(self.filename, self.image, optical=CAROUSEL)
        optical, label = tiff.read(self.filename, sims=False,
                                   optical=True, label=True)
        np.testing.assert_array_equal(optical, CAROUSEL)
        np.testing.assert_array_equal(label, LABEL)

        optical_only = tiff.read(self.filename, sims=False, optical=True)
        np.testing.assert_array_equal(optical_only, CAROUSEL)

        label_only = tiff.read(self.filename, sims=False, label=True)
        np.testing.assert_array_equal(label_only, LABEL)

    def test_write_invalid_input(self):
        # not MibiImage
        with self.assertRaises(ValueError):
            tiff.write(self.filename, DATA)
        # no coordinates
        metadata = METADATA.copy()
        del metadata['coordinates']
        image = mi.MibiImage(DATA, CHANNELS, **metadata)
        with self.assertRaises(ValueError):
            tiff.write(self.filename, image)
        # no size
        metadata = METADATA.copy()
        del metadata['size']
        image = mi.MibiImage(DATA, CHANNELS, **metadata)
        with self.assertRaises(ValueError):
            tiff.write(self.filename, image)
        # string rather than tuple channels
        channels = [c[1] for c in CHANNELS]
        image = mi.MibiImage(DATA, channels, **METADATA)
        with self.assertRaises(ValueError):
            tiff.write(self.filename, image)

    def test_read_wrong_software_tag(self):
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', message='.*low contrast image.*')
            io.imsave(self.filename, DATA)
        with self.assertRaises(ValueError):
            tiff.read(self.filename)

    def test_read_with_invalid_return_types(self):
        tiff.write(self.filename, self.image)
        with self.assertRaises(ValueError):
            tiff.read(self.filename, sims=False)

    def test_read_metadata_only(self):
        tiff.write(self.filename, self.image)
        metadata = tiff.info(self.filename)
        expected = METADATA.copy()
        expected.update({
            'conjugates': list(CHANNELS),
            'date': datetime.datetime.strptime(expected['date'],
                                               '%Y-%m-%dT%H:%M:%S')
        })
        self.assertEqual(metadata, expected)

    def test_sort_channels_before_writing(self):

        # Unordered indices: [2, 0, 4, 1, 3]
        unordered_channels = ((3, 'Target3'), (1, 'Target1'), (5, 'Target5'),
                              (2, 'Target2'), (4, 'Target4'))
        unordered_data = np.stack([DATA[:, :, 2], DATA[:, :, 0], DATA[:, :, 4],
                                   DATA[:, :, 1], DATA[:, :, 3]], axis=2)
        unordered_image = mi.MibiImage(unordered_data, unordered_channels,
                                       **METADATA)

        tiff.write(self.filename, unordered_image)
        image = tiff.read(self.filename)
        self.assertEqual(image, self.image)

    def test_write_single_channel_tiffs(self):

        basepath = os.path.split(self.filename)[0]

        tiff.write(basepath, self.image, multichannel=False)

        for i, (_, channel) in enumerate(CHANNELS):
            formatted = util.format_for_filename(channel)
            filename = os.path.join(basepath, '{}.tiff'.format(formatted))

            tif = tiff.read(filename)

            np.testing.assert_equal(np.squeeze(tif.data), DATA[:, :, i])
            self.assertTupleEqual(tif.channels, (CHANNELS[i], ))
            self.assertEqual(tif.data.dtype, np.uint16)

    def test_write_float_tiff(self):

        tiff.write(self.filename, self.image,
                   multichannel=True, write_float=True)
        image = tiff.read(self.filename)
        self.assertEqual(image.data.dtype, np.float32)
        np.testing.assert_equal(image.data, self.image.data.astype(np.float32))


if __name__ == '__main__':
    unittest.main()
