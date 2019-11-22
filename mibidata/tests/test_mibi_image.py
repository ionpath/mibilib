"""Tests for mibidata.mibi_image

Copyright (C) 2019 Ionpath, Inc.  All rights reserved."""

import datetime
import os
import shutil
import tempfile
import unittest
import warnings

import numpy as np
from skimage import io as skio, transform

from mibidata import mibi_image as mi

TEST_DATA = np.arange(12).reshape(2, 2, 3)
STRING_LABELS = ('1', '2', '3')
TUPLE_LABELS = (
    ('Mass1', 'Target1'), ('Mass2', 'Target2'), ('Mass3', 'Target3'))
MASS_LABELS = ('Mass1', 'Mass2', 'Mass3')
MASS_INTEGERS = (1, 2, 3)
TARGET_LABELS = ('Target1', 'Target2', 'Target3')
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
    'version': 'alpha'
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


class TestMibiImage(unittest.TestCase):

    def setUp(self):
        # We have set anti-aliasing explicitly to False in MibiImage.resize
        warnings.filterwarnings(
            'ignore',
            message='Anti-aliasing will be enabled by default.*')
        self.maxDiff = None

    def test_mibi_image_string_labels(self):
        image = mi.MibiImage(TEST_DATA, STRING_LABELS)
        np.testing.assert_array_equal(image.data, TEST_DATA)
        self.assertEqual(image.channels, STRING_LABELS)
        self.assertIsNone(image.masses)
        self.assertIsNone(image.targets)

    def test_mibi_image_tuple_labels(self):
        image = mi.MibiImage(TEST_DATA, TUPLE_LABELS)
        np.testing.assert_array_equal(image.data, TEST_DATA)
        self.assertEqual(image.channels, TUPLE_LABELS)
        self.assertEqual(image.masses, MASS_LABELS)
        self.assertEqual(image.targets, TARGET_LABELS)

    def test_data_channel_length_mismatch(self):
        with self.assertRaises(ValueError):
            mi.MibiImage(TEST_DATA, STRING_LABELS[:2])

    def test_non_unique_channels(self):
        with self.assertRaises(ValueError):
            mi.MibiImage(TEST_DATA, ['1', '2', '1'])
        with self.assertRaises(ValueError):
            mi.MibiImage(TEST_DATA, [('1', 'A'), ('2', 'B'), ('3', 'A')])
        with self.assertRaises(ValueError):
            mi.MibiImage(TEST_DATA, [('1', 'A'), ('2', 'B'), ('2', 'C')])

    def test_string_datetime(self):
        image = mi.MibiImage(TEST_DATA, TUPLE_LABELS, **METADATA)
        self.assertEqual(datetime.datetime(2017, 9, 16, 15, 26, 0), image.date)

    def test_obj_datetime(self):
        date = datetime.datetime(2017, 9, 17, 15, 26, 0)
        image = mi.MibiImage(TEST_DATA, TUPLE_LABELS, date=date)
        self.assertEqual(image.date, date)

    def test_set_channels(self):
        image = mi.MibiImage(TEST_DATA, TUPLE_LABELS)
        image.channels = TUPLE_LABELS
        self.assertEqual(image.masses, MASS_LABELS)

    def test_set_channels_ints(self):
        image = mi.MibiImage(TEST_DATA, TUPLE_LABELS)
        with self.assertRaises(ValueError):
            image.channels = MASS_INTEGERS

    def test_set_channels_invalid_tuple(self):
        image = mi.MibiImage(TEST_DATA, TUPLE_LABELS)
        invalid_tuple_1 = [(c, ) for c in STRING_LABELS]
        invalid_tuple_3 = [(c, 'a', 'b') for c in STRING_LABELS]
        with self.assertRaises(ValueError):
            image.channels = invalid_tuple_1
        with self.assertRaises(ValueError):
            image.channels = invalid_tuple_3

    def test_backwards_compatibility_with_old_metadata(self):
        with self.assertWarns(UserWarning):
            image = mi.MibiImage(TEST_DATA, TUPLE_LABELS, **OLD_METADATA)
        self.assertEqual(image.fov_id, OLD_METADATA['folder'].split('/')[0])
        self.assertEqual(image.fov_name, OLD_METADATA['point_name'])
        self.assertEqual(image.point_name, OLD_METADATA['point_name'])
        self.assertEqual(image._user_defined_attributes, ['point_name'])

    def test_check_fov_id(self):
        image = mi.MibiImage(TEST_DATA, TUPLE_LABELS)
        image.fov_id = 'Point2'
        image.folder = 'Point2/RowNumber0/Depth_Profile0'
        image.fov_name = 'R1C3_Tonsil'
        with self.assertRaises(ValueError):
            image.fov_id = 'Point99'
        with self.assertRaises(ValueError):
            image.fov_id = None

    def test_equality(self):
        first = mi.MibiImage(TEST_DATA, STRING_LABELS)
        second = mi.MibiImage(TEST_DATA.copy(), STRING_LABELS)
        self.assertTrue(first == second)

    def test_dtype_inequality(self):
        first = mi.MibiImage(TEST_DATA, STRING_LABELS)
        second = mi.MibiImage(TEST_DATA.astype(np.float), STRING_LABELS)
        self.assertFalse(first == second)

    def test_label_inequality(self):
        first = mi.MibiImage(TEST_DATA, STRING_LABELS)
        second = mi.MibiImage(TEST_DATA, TARGET_LABELS)
        self.assertFalse(first == second)

    def test_data_inequality(self):
        first = mi.MibiImage(TEST_DATA, STRING_LABELS)
        second = mi.MibiImage(TEST_DATA.copy(), STRING_LABELS)
        second.data[0, 0, 0] = 1
        self.assertFalse(first == second)

    def test_metadata_inequality(self):
        first = mi.MibiImage(TEST_DATA, STRING_LABELS, **METADATA)
        second = mi.MibiImage(TEST_DATA.copy(), STRING_LABELS)
        self.assertFalse(first == second)

    def test_getitem(self):
        image = mi.MibiImage(TEST_DATA, STRING_LABELS)
        np.testing.assert_array_equal(image['2'], image.slice_data('2'))
        np.testing.assert_array_equal(
            image[['1', '2']], image.slice_data(['1', '2']))

    def test_metadata(self):
        image = mi.MibiImage(TEST_DATA, TUPLE_LABELS, **METADATA)
        metadata = METADATA.copy()
        metadata['date'] = datetime.datetime.strptime(metadata['date'],
                                                      mi._DATETIME_FORMAT)
        self.assertEqual(image.metadata(), metadata)

    def test_metadata_with_user_defined_metadata_in_instantiation(self):
        image = mi.MibiImage(TEST_DATA, TUPLE_LABELS, **METADATA,
                             **USER_DEFINED_METADATA)
        metadata = METADATA.copy()
        metadata.update(USER_DEFINED_METADATA)
        metadata['date'] = datetime.datetime.strptime(metadata['date'],
                                                      mi._DATETIME_FORMAT)
        self.assertEqual(image.metadata(), metadata)

    def test_retrieve_user_defined_attributes(self):
        image = mi.MibiImage(TEST_DATA, TUPLE_LABELS, **USER_DEFINED_METADATA)
        self.assertEqual(image.mass_range, 20) # pylint: disable=no-member
        self.assertEqual(image.x_size, 500.) # pylint: disable=no-member
        self.assertEqual(image.y_size, 500.) # pylint: disable=no-member

    def test_capture_of_user_defined_metadata(self):
        image = mi.MibiImage(TEST_DATA, TUPLE_LABELS, **METADATA,
                             **USER_DEFINED_METADATA)
        self.assertEqual(image._user_defined_attributes,
                         list(USER_DEFINED_METADATA))

    def test_metadata_wrong_fov_id(self):
        metadata = METADATA.copy()
        metadata = {**metadata, **USER_DEFINED_METADATA}
        metadata['fov_id'] = 'Point99'
        with self.assertRaises(ValueError):
            mi.MibiImage(TEST_DATA, TUPLE_LABELS, **metadata)

    def test_channel_inds_single_channel(self):
        image = mi.MibiImage(TEST_DATA, STRING_LABELS)
        np.testing.assert_array_equal(image.channel_inds('2'), 1)

    def test_channel_inds_channel_list(self):
        image = mi.MibiImage(TEST_DATA, STRING_LABELS)
        np.testing.assert_array_equal(
            image.channel_inds(np.array(['1', '3'])),
            np.array([0, 2]))

    def test_channel_inds_single_mass(self):
        image = mi.MibiImage(TEST_DATA, TUPLE_LABELS)
        np.testing.assert_array_equal(image.channel_inds('Mass2'), 1)

    def test_channel_inds_mass_list(self):
        image = mi.MibiImage(TEST_DATA, TUPLE_LABELS)
        np.testing.assert_array_equal(
            image.channel_inds(np.array(['Mass1', 'Mass3'])),
            np.array([0, 2]))

    def test_channel_inds_single_target(self):
        image = mi.MibiImage(TEST_DATA, TUPLE_LABELS)
        np.testing.assert_array_equal(image.channel_inds('Mass2'), 1)

    def test_channel_inds_target_list(self):
        image = mi.MibiImage(TEST_DATA, TUPLE_LABELS)
        np.testing.assert_array_equal(
            image.channel_inds(np.array(['Mass1', 'Mass3'])),
            np.array([0, 2]))

    def test_channel_inds_key_error(self):
        image = mi.MibiImage(TEST_DATA, STRING_LABELS)
        with self.assertRaises(KeyError):
            image.channel_inds(np.array(['1', '4']))

    def test_slice_data(self):
        # Test slicing out single layer.
        im = mi.MibiImage(TEST_DATA, STRING_LABELS)
        np.testing.assert_array_equal(im.slice_data('2'), TEST_DATA[:, :, 1])
        np.testing.assert_array_equal(im.slice_data(['2']),
                                      TEST_DATA[:, :, [1]])
        # Test slicing out multiple layers.
        np.testing.assert_array_equal(im.slice_data(['3', '1']),
                                      TEST_DATA[:, :, [2, 0]])

    def test_slice_empty_list_from_image(self):
        image = mi.MibiImage(TEST_DATA, STRING_LABELS)
        empty_data = image.slice_data([])
        self.assertEqual(empty_data.shape[2], 0)
        # confirm that this object will be interpreted as False by if:
        self.assertFalse(empty_data)

    def test_slice_image(self):
        image = mi.MibiImage(TEST_DATA, STRING_LABELS)
        image_slice = image.slice_image(['1', '3'])
        self.assertEqual(
            image_slice,
            mi.MibiImage(image.slice_data(['1', '3']), ['1', '3']))

        single_slice = image.slice_image('2')
        self.assertEqual(
            single_slice,
            mi.MibiImage(image.slice_data(['2']), ['2']))

    def test_copy(self):
        first = mi.MibiImage(TEST_DATA, STRING_LABELS)
        second = first.copy()
        self.assertTrue(first == second)
        second.data[:, :, 0] = 0
        np.testing.assert_array_equal(first.data, TEST_DATA)

    def test_append(self):
        first_image = mi.MibiImage(TEST_DATA[:, :, :2], ['1', '2'],
                                   **METADATA)
        second_image = mi.MibiImage(TEST_DATA[:, :, 1:3], ['3', '4'])
        first_image.append(second_image)
        expected = mi.MibiImage(TEST_DATA[:, :, [0, 1, 1, 2]],
                                ['1', '2', '3', '4'], **METADATA)
        self.assertEqual(first_image, expected)
        np.testing.assert_array_equal(
            first_image.slice_data('4'), second_image.slice_data('4'))

    def test_remove_layers_without_copy(self):
        image = mi.MibiImage(TEST_DATA, STRING_LABELS, **METADATA)
        image.remove_channels(['1', '3'])
        np.testing.assert_array_equal(image.data, TEST_DATA[:, :, [1]])
        self.assertEqual(image.channels, tuple('2'))
        metadata = METADATA.copy()
        metadata['date'] = datetime.datetime.strptime(metadata['date'],
                                                      mi._DATETIME_FORMAT)
        self.assertEqual(image.metadata(), metadata)

    def test_remove_layers_with_copy(self):
        image = mi.MibiImage(TEST_DATA, STRING_LABELS)
        new_image = image.remove_channels(['1', '3'], copy=True)
        np.testing.assert_array_equal(new_image.data, TEST_DATA[:, :, [1]])
        self.assertEqual(new_image.channels, tuple('2'))
        # check have not altered original image
        np.testing.assert_array_equal(image.data, TEST_DATA)
        self.assertEqual(image.channels, STRING_LABELS)

    def test_resize_integer_without_copy(self):
        image = mi.MibiImage(np.random.rand(5, 5, 3), STRING_LABELS)
        data = image.data
        image.resize(3)
        expected = transform.resize(data, (3, 3, 3), order=3, mode='edge')
        self.assertTrue(image == mi.MibiImage(expected, STRING_LABELS))

    def test_resize_tuple_without_copy(self):
        image = mi.MibiImage(np.random.rand(5, 5, 3), STRING_LABELS)
        data = image.data
        image.resize((3, 3))
        expected = transform.resize(data, (3, 3, 3), order=3, mode='edge')
        self.assertTrue(image == mi.MibiImage(expected, STRING_LABELS))

    def test_resize_integer_with_copy(self):
        image = mi.MibiImage(np.random.rand(5, 5, 3), STRING_LABELS)
        image_copy = mi.MibiImage(image.data.copy(), STRING_LABELS)
        resized = image.resize(3, copy=True)
        expected = transform.resize(image.data, (3, 3, 3), order=3, mode='edge')
        self.assertTrue(resized == mi.MibiImage(expected, STRING_LABELS))
        self.assertTrue(image == image_copy)

    def test_resize_preserve_uint_dtype(self):
        image = mi.MibiImage(
            np.random.randint(0, 255, (5, 5, 3)).astype(np.uint8),
            STRING_LABELS)
        data = image.data
        image.resize(3, preserve_type=True)
        expected = transform.resize(data, (3, 3, 3), order=3, mode='edge',
                                    preserve_range=True).astype(np.uint8)
        self.assertTrue(image == mi.MibiImage(expected, STRING_LABELS))

    def test_resize_preserve_float_dtype(self):
        image = mi.MibiImage(np.random.rand(5, 5, 3), STRING_LABELS)
        data = image.data
        image.resize(3, preserve_type=True)
        # The return value should not be affected by whether the
        # dtype is preserved if the input data are floats in the unit interval.
        expected = transform.resize(data, (3, 3, 3), order=3, mode='edge')
        self.assertTrue(image == mi.MibiImage(expected, STRING_LABELS))

    def test_resize_to_larger(self):
        image = mi.MibiImage(np.random.rand(5, 5, 3), STRING_LABELS)
        expected = mi.MibiImage(
            transform.resize(image.data, (6, 6, 3), order=3, mode='edge'),
            STRING_LABELS)
        image.resize(6)
        self.assertTrue(image == expected)

    def test_resize_bad_integer_aspect_ratio(self):
        image = mi.MibiImage(np.random.rand(5, 4, 3), STRING_LABELS)
        with self.assertRaises(ValueError):
            image.resize(3)

    def test_resize_bad_tuple_aspect_ratio(self):
        image = mi.MibiImage(np.random.rand(5, 4, 3), STRING_LABELS)
        with self.assertRaises(ValueError):
            image.resize((4, 4))


class TestExportGrayscales(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _test_export_image_helper(self, array, expected):
        channels = ['1', '2']
        im = mi.MibiImage(array, channels)
        im.export_pngs(self.test_dir)
        for i, label in enumerate(channels):
            roundtripped = skio.imread(
                f'{os.path.join(self.test_dir, label)}.png')
            np.testing.assert_array_equal(roundtripped, expected[:, :, i])

    def test_export_uint8_image(self):
        data = np.random.randint(0, 255, (10, 10, 2)).astype(np.uint8)
        self._test_export_image_helper(data, data)

    def test_export_low_uint16_image(self):
        data = np.random.randint(0, 255, (10, 10, 2)).astype(np.uint16)
        self._test_export_image_helper(data, data)

    def test_export_high_uint16_image(self):
        data = np.random.randint(
            256, 2 ** 16 - 1, (10, 10, 2)).astype(np.uint16)
        self._test_export_image_helper(data, data)

    def test_export_int_in_uint8_range_image(self):
        data = np.random.randint(0, 255, (10, 10, 2)).astype(np.int32)
        self._test_export_image_helper(data, data)

    def test_export_int_in_uint16_range_image(self):
        data = np.random.randint(256, 2 ** 16 - 1, (10, 10, 2)).astype(np.int64)
        self._test_export_image_helper(data, data)

    def test_export_bool_image(self):
        data = np.random.randint(0, 1, (10, 10, 2)).astype(np.bool)
        self._test_export_image_helper(data, data)

    def test_export_int_below_uint16_range_image(self):
        array = np.random.randint(-10, -1, (10, 10, 2))
        im = mi.MibiImage(array, ['1', '2'])
        with self.assertRaises(TypeError):
            im.export_pngs('path')

    def test_export_int_above_uint16_range_image(self):
        array = np.random.randint(2 ** 16, 2 ** 16 + 1, (10, 10, 2))
        im = mi.MibiImage(array, ['1', '2'])
        with self.assertRaises(TypeError):
            im.export_pngs('path')

    def test_export_float_unit_interval_image(self):
        data = np.random.randint(0, 1, (10, 10, 2)).astype(np.float32)
        with self.assertRaises(TypeError):
            self._test_export_image_helper(data, 255 * data)

    def test_export_float_outside_unit_interval(self):
        array = np.random.rand(10, 10, 2) + 1.
        im = mi.MibiImage(array, ['1', '2'])
        with self.assertRaises(TypeError):
            im.export_pngs('path')

    def test_export_other_type(self):
        array = np.random.randint(0, 10, (10, 10, 2)).astype(np.complex)
        im = mi.MibiImage(array, ['1', '2'])
        with self.assertRaises(TypeError):
            im.export_pngs('path')

    def test_error_when_saving_uint16_png(self):
        array = np.random.randint(0, 255, (10, 10, 2)).astype(np.uint16)
        im = mi.MibiImage(array, ['1', '2'])
        with self.assertRaises(IOError):
            im.export_pngs('path')

    def test_export_resized_pngs(self):
        im = mi.MibiImage(
            np.random.randint(0, 255, (10, 10, 2)).astype(np.uint16),
            ['1', '2'])
        resized = im.resize(5, copy=True, preserve_type=True)
        im.export_pngs(self.test_dir, size=5)
        images = [skio.imread(f'{os.path.join(self.test_dir, label)}.png')
                  for label in im.channels]
        for i, roundtripped in enumerate(images):
            np.testing.assert_array_equal(
                roundtripped, resized.data[:, :, i])

    def test_export_with_tuple_channel_names(self):
        channels = [(1, 'Channel_1'), (2, 'Channel/2')]
        data = np.random.randint(0, 255, (10, 10, 2)).astype(np.uint16)
        im = mi.MibiImage(data, channels)
        im.export_pngs(self.test_dir)
        images = [skio.imread(f'{os.path.join(self.test_dir,  label)}.png')
                  for label in ('Channel_1', 'Channel-2')]
        for i, roundtripped in enumerate(images):
            np.testing.assert_array_equal(
                roundtripped, im.data[:, :, i])

    def test_rename_targets_tuple_channels(self):
        masses = [1, 2, 3]
        targets = ['Channel1', 'Channel2', 'Channel3']
        data = np.random.randint(0, 255, (10, 10, 3)).astype(np.uint16)
        im = mi.MibiImage(data, list(zip(masses, targets)))

        channel_map = {
            'Channel2': 'Channel2 - Renamed',
            'Channel3': 'Channel3 - Renamed'}
        im.rename_targets(channel_map)

        expected_targets = [
            'Channel1',
            'Channel2 - Renamed',
            'Channel3 - Renamed']

        self.assertTupleEqual(im.channels, tuple(zip(masses, expected_targets)))

    def test_rename_targets_targets_only(self):
        targets = ['Channel1', 'Channel2', 'Channel3']
        data = np.random.randint(0, 255, (10, 10, 3)).astype(np.uint16)
        im = mi.MibiImage(data, targets)

        channel_map = {
            'Channel2': 'Channel2 - Renamed',
            'Channel3': 'Channel3 - Renamed'}
        im.rename_targets(channel_map)

        expected_targets = [
            'Channel1',
            'Channel2 - Renamed',
            'Channel3 - Renamed']

        self.assertTupleEqual(im.channels, tuple(expected_targets))

    def test_rename_targets_missing_target(self):
        targets = ['Channel1', 'Channel2', 'Channel3']
        data = np.random.randint(0, 255, (10, 10, 3)).astype(np.uint16)
        im = mi.MibiImage(data, targets)

        channel_map = {
            'Channel2': 'Channel2 - Renamed',
            'i_dont_exist': 'Channel3 - Renamed'}

        with self.assertRaises(KeyError):
            im.rename_targets(channel_map)

if __name__ == '__main__':
    unittest.main()
