"""Tests for mibidata.tiff

Copyright (C) 2019 Ionpath, Inc.  All rights reserved."""

import datetime
import os
import shutil
import tempfile
import unittest
import warnings

import numpy as np
from skimage import io as skio, img_as_ubyte, transform
from skimage.external.tifffile import TiffFile

from mibidata import mibi_image as mi
from mibidata import tiff, util

DATA = np.arange(500).reshape(10, 10, 5).astype(np.float32)
SED = np.arange(100).reshape(10, 10)
CAROUSEL = np.random.randint(0, 255, (4096, 4096, 3), np.uint8)
X_COORD, Y_COORD = tiff._BOTTOM_LABEL_COORDINATES
LABEL = (img_as_ubyte(transform.rotate(
    CAROUSEL[X_COORD[0]:X_COORD[1], Y_COORD[0]:Y_COORD[1]], 270)))
CHANNELS = ((1, 'Target1'), (2, 'Target2'), (3, 'Target3'),
            (4, 'Target4'), (5, 'Target5'))
METADATA = {
    'run': '20180703_1234_test', 'date': '2017-09-16T15:26:00',
    'coordinates': (12345, -67890), 'size': 500., 'slide': '857',
    'fov_id': 'Point1', 'fov_name': 'R1C3_Tonsil',
    'folder': 'Point1/RowNumber0/Depth_Profile0',
    'dwell': 4, 'scans': '0,5', 'aperture': '300um',
    'instrument': 'MIBIscope1', 'tissue': 'Tonsil',
    'panel': '20170916_1x', 'mass_offset': 0.1, 'mass_gain': 0.2,
    'time_resolution': 0.5, 'miscalibrated': False, 'check_reg': False,
    'filename': '20180703_1234_test', 'description': 'test image',
    'version': 'alpha',
}
USER_DEFINED_METADATA = {'x_size': 500., 'y_size': 500., 'mass_range': 20}
OLD_METADATA = {
    'run': '20180703_1234_test', 'date': '2017-09-16T15:26:00',
    'coordinates': (12345, -67890), 'size': 500., 'slide': '857',
    'point_name': 'R1C3_Tonsil', 'dwell': 4, 'scans': '0,5',
    'folder': 'Point1/RowNumber0/Depth_Profile0',
    'aperture': '300um', 'instrument': 'MIBIscope1', 'tissue': 'Tonsil',
    'panel': '20170916_1x', 'version': None, 'mass_offset': 0.1,
    'mass_gain': 0.2, 'time_resolution': 0.5, 'miscalibrated': False,
    'check_reg': False, 'filename': '20180703_1234_test'
}
OLD_TIFF_FILE = os.path.join(os.path.dirname(__file__), 'data', 'v0.1.tiff')


class TestTiffHelpers(unittest.TestCase):

    def test_motor_to_cm(self):
        self.assertEqual(tiff._micron_to_cm(10000), (1, 1))

    def test_cm_to_motor(self):
        self.assertEqual(tiff._cm_to_micron((1, 1)), 10000)


class TestWriteReadTiff(unittest.TestCase):

    def setUp(self):
        self.float_image = mi.MibiImage(DATA, CHANNELS, **METADATA)
        self.int_image = mi.MibiImage(
            DATA.astype(np.uint16), CHANNELS, **METADATA)
        self.image_user_defined_metadata = mi.MibiImage(DATA, CHANNELS,
                                                        **METADATA,
                                                        **USER_DEFINED_METADATA)
        self.image_old_metadata = mi.MibiImage(
            DATA, CHANNELS, **OLD_METADATA)
        self.folder = tempfile.mkdtemp()
        self.filename = os.path.join(self.folder, 'test.tiff')
        self.maxDiff = None

    def tearDown(self):
        shutil.rmtree(self.folder)

    def test_current_software_version(self):
        self.assertEqual(tiff.SOFTWARE_VERSION, 'IonpathMIBIv1.0')

    def test_sims_only(self):
        tiff.write(self.filename, self.float_image)
        image = tiff.read(self.filename)
        self.assertEqual(image, self.float_image)
        sims, sed, optical, label = tiff.read(self.filename, sed=True,
                                              optical=True, label=True)
        self.assertEqual(sims, self.float_image)
        self.assertIsNone(sed)
        self.assertIsNone(optical)
        self.assertIsNone(label)
        self.assertEqual(image.data.dtype, np.float32)

    def test_default_ranges(self):
        tiff.write(self.filename, self.float_image)
        with TiffFile(self.filename) as tif:
            for i, page in enumerate(tif.pages):
                self.assertEqual(page.tags['smin_sample_value'].value, 0)
                self.assertEqual(page.tags['smax_sample_value'].value,
                                 self.float_image.data[:, :, i].max())

    def test_custom_ranges(self):
        ranges = list(zip([1]*5, range(2, 7)))
        tiff.write(self.filename, self.float_image, ranges=ranges)
        with TiffFile(self.filename) as tif:
            for i, page in enumerate(tif.pages):
                self.assertEqual(page.tags['smin_sample_value'].value,
                                 ranges[i][0])
                self.assertEqual(page.tags['smax_sample_value'].value,
                                 ranges[i][1])


    def test_sims_and_sed(self):
        tiff.write(self.filename, self.float_image, sed=SED)
        image = tiff.read(self.filename)
        self.assertEqual(image, self.float_image)
        sims, sed, optical, label = tiff.read(self.filename, sed=True,
                                              optical=True, label=True)
        self.assertEqual(sims, self.float_image)
        np.testing.assert_array_equal(sed, SED)
        self.assertIsNone(optical)
        self.assertIsNone(label)

    def test_sims_and_sed_and_optical_and_label(self):
        tiff.write(self.filename, self.float_image, sed=SED, optical=CAROUSEL)
        image, sed, optical, label = tiff.read(self.filename, sed=True,
                                               optical=True, label=True)
        self.assertEqual(image, self.float_image)
        np.testing.assert_array_equal(sed, SED)
        np.testing.assert_array_equal(optical, CAROUSEL)
        np.testing.assert_array_equal(label, LABEL)

    def test_read_sed_only(self):
        tiff.write(self.filename, self.float_image, sed=SED)
        sed = tiff.read(self.filename, sims=False, sed=True)
        np.testing.assert_array_equal(sed, SED)

    def test_read_optical_and_label_only(self):
        tiff.write(self.filename, self.float_image, optical=CAROUSEL)
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
            skio.imsave(self.filename, DATA)
        with self.assertRaises(ValueError):
            tiff.read(self.filename)

    def test_read_with_invalid_return_types(self):
        tiff.write(self.filename, self.float_image)
        with self.assertRaises(ValueError):
            tiff.read(self.filename, sims=False)

    def test_read_metadata_only(self):
        tiff.write(self.filename, self.float_image)
        metadata = tiff.info(self.filename)
        expected = METADATA.copy()
        expected.update({
            'conjugates': list(CHANNELS),
            'date': datetime.datetime.strptime(expected['date'],
                                               '%Y-%m-%dT%H:%M:%S')})
        self.assertEqual(metadata, expected)

    def test_read_metadata_with_user_defined_metadata(self):
        tiff.write(self.filename, self.image_user_defined_metadata)
        metadata = tiff.info(self.filename)
        expected = METADATA.copy()
        expected.update({
            'conjugates': list(CHANNELS),
            'date': datetime.datetime.strptime(expected['date'],
                                               '%Y-%m-%dT%H:%M:%S'),
            **USER_DEFINED_METADATA})
        self.assertEqual(metadata, expected)

    def test_read_old_metadata(self):
        tiff.write(self.filename, self.image_old_metadata)
        metadata = tiff.info(self.filename)
        expected = METADATA.copy()
        expected.update({
            'point_name': OLD_METADATA['point_name'],
            'conjugates': list(CHANNELS),
            'date': datetime.datetime.strptime(expected['date'],
                                               '%Y-%m-%dT%H:%M:%S'),
            'description': None, 'version': None})
        self.assertEqual(metadata, expected)

    def test_open_file_with_old_metadata(self):
        metadata = tiff.info(OLD_TIFF_FILE)
        expected = METADATA.copy()
        expected.update({
            'conjugates': list(CHANNELS),
            'date': datetime.datetime.strptime(expected['date'],
                                               '%Y-%m-%dT%H:%M:%S'),
        })
        del expected['description']
        del expected['version']
        self.assertEqual(metadata, expected)

    def test_convert_from_previous(self):
        description = {'mibi.description': OLD_METADATA['point_name'],
                       'mibi.folder': OLD_METADATA['folder']}
        tiff._convert_from_previous(description)
        self.assertEqual(description,
                         {'mibi.fov_name': OLD_METADATA['point_name'],
                          'mibi.folder': OLD_METADATA['folder'],
                          'mibi.fov_id': OLD_METADATA['folder'].split('/')[0]})

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
        self.assertEqual(image, self.float_image)

    def test_write_single_channel_tiffs(self):

        basepath = os.path.split(self.filename)[0]

        tiff.write(basepath, self.float_image, multichannel=False)

        for i, (_, channel) in enumerate(CHANNELS):
            formatted = util.format_for_filename(channel)
            filename = os.path.join(basepath, '{}.tiff'.format(formatted))

            tif = tiff.read(filename)

            np.testing.assert_equal(np.squeeze(tif.data), DATA[:, :, i])
            self.assertTupleEqual(tif.channels, (CHANNELS[i], ))
            self.assertEqual(tif.data.dtype, np.float32)

    def test_tiff_dtype_correct_arguments(self):
        supported_dtypes = [np.float32, np.uint16]
        for dtype in supported_dtypes:
            tiff.write(self.filename, self.float_image, multichannel=True,
                       dtype=dtype)

        unsupported_types = ['abcdef', np.str, np.bool, np.uint8, np.float64]
        for dtype in unsupported_types:
            with self.assertRaises(ValueError):
                tiff.write(self.filename, self.float_image, multichannel=True,
                           dtype=dtype)

    def test_write_float_is_deprecated(self):
        with self.assertRaises(ValueError):
            tiff.write(self.filename, self.int_image, write_float=True)
        with self.assertRaises(ValueError):
            tiff.write(self.filename, self.float_image, write_float=False)

    def test_write_float32_from_float32_tiff_dtype_none(self):
        tiff.write(self.filename, self.float_image, multichannel=True)
        image = tiff.read(self.filename)
        self.assertEqual(image.data.dtype, np.float32)
        np.testing.assert_equal(
            image.data, self.float_image.data.astype(np.float32))

    def test_write_float32_from_float32_dtype_np_float32(self):
        tiff.write(self.filename, self.float_image, multichannel=True,
                   dtype=np.float32)
        image = tiff.read(self.filename)
        self.assertEqual(image.data.dtype, np.float32)
        np.testing.assert_equal(
            image.data, self.float_image.data.astype(np.float32))

    def test_write_float32_from_int_dtype_np_float32(self):
        tiff.write(self.filename, self.int_image, multichannel=True,
                   dtype=np.float32)
        image = tiff.read(self.filename)
        self.assertEqual(image.data.dtype, np.float32)
        np.testing.assert_equal(
            image.data, self.float_image.data.astype(np.float32))

    def test_write_uint16_from_uint16_dtype_none(self):
        tiff.write(self.filename, self.int_image, multichannel=True)
        image = tiff.read(self.filename)
        self.assertEqual(image.data.dtype, np.uint16)
        np.testing.assert_equal(
            image.data, self.float_image.data.astype(np.uint16))

    def test_write_uint16_from_uint16_dtype_np_uint16(self):
        tiff.write(self.filename, self.int_image, multichannel=True,
                   dtype=np.uint16)
        image = tiff.read(self.filename)
        self.assertEqual(image.data.dtype, np.uint16)
        np.testing.assert_equal(
            image.data, self.float_image.data.astype(np.uint16))

    def test_write_uint16_from_float32_dtype_np_uint16(self):
        tiff.write(self.filename, self.float_image, multichannel=True,
                   dtype=np.uint16)
        image = tiff.read(self.filename)
        self.assertEqual(image.data.dtype, np.uint16)
        np.testing.assert_equal(
            image.data, self.float_image.data.astype(np.uint16))

    def test_write_float32_as_uint16_fails(self):
        lossy_image = mi.MibiImage(DATA + 0.001, CHANNELS, **METADATA)
        with self.assertRaises(ValueError):
            tiff.write(self.filename, lossy_image, multichannel=True,
                       dtype=np.uint16)

    def test_write_float32_from_float64(self):
        float64_image = mi.MibiImage(
            DATA.astype(np.float64), CHANNELS, **METADATA)
        tiff.write(self.filename, float64_image, multichannel=True)
        image = tiff.read(self.filename)
        np.testing.assert_equal(image.data, DATA)
        self.assertEqual(image.data.dtype, np.float32)

    def test_write_uint16_from_uint8(self):
        uint8_image = mi.MibiImage(
            np.random.randint(0, 256, (32, 32, 5), dtype=np.uint8),
            CHANNELS, **METADATA)
        tiff.write(self.filename, uint8_image, multichannel=True)
        image = tiff.read(self.filename)
        np.testing.assert_equal(image.data, uint8_image.data.astype(np.uint16))
        self.assertEqual(image.data.dtype, np.uint16)


if __name__ == '__main__':
    unittest.main()
