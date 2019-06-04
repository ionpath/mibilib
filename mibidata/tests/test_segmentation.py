"""Tests for mibidata.segmentation

Copyright (C) 2019 Ionpath, Inc.  All rights reserved."""

import unittest

import numpy as np
from numpy.testing import assert_array_equal
import pandas as pd
import pandas.util.testing as pdt

from mibidata import mibi_image as mi, segmentation


class TestSegmentation(unittest.TestCase):

    def setUp(self):
        np.random.seed(seed=20160906)

    def test_quadrant_mean(self):
        data = np.stack((
            np.array([
                [3, 2, 4],
                [1, 1, 3],
                [0, 0, 1]]),
            np.array([
                [0, 0, 1],
                [0, 0, 0],
                [0, 0, 2]]),
        ), axis=2)
        # assume labels are for cell ID 1, such as with label image:
        # np.array([
        #     [0, 1, 1],
        #     [1, 1, 1],
        #     [0, 0, 0]
        # ])
        inds = ((0, 0, 1, 1, 1), (1, 2, 0, 1, 2))
        quads_channel_0 = np.power(2 * 4 * (1 + 1) * 3, 1 / 4) # pylint: disable=assignment-from-no-return
        quads_channel_1 = np.power(0 * 1 * (0 + 0) * 0, 1 / 4) # pylint: disable=assignment-from-no-return
        expected = np.array((quads_channel_0, quads_channel_1))
        assert_array_equal(
            segmentation._quadrant_mean(inds, mi.MibiImage(data, ['1', '2'])),
            expected
        )

    def test_extract_cell_dataframe(self):
        data = np.stack((
            np.array([
                [3, 2, 4, 0],
                [1, 1, 3, 1],
                [0, 0, 1, 1],
                [5, 0, 3, 1]]),
            np.array([
                [0, 0, 1, 0],
                [0, 0, 0, 1],
                [0, 0, 2, 0],
                [5, 0, 0, 0]]),
            ), axis=2)
        cell_labels = np.array([
            [0, 1, 1, 0],
            [1, 1, 3, 3],
            [0, 0, 3, 3],
            [0, 0, 3, 3]
        ])
        image = mi.MibiImage(data, ['1', '2'])
        labels = [1, 3]
        areas = [4, 6]
        x_centroids = [1, 2]
        y_centroids = [0, 2]
        first_total = [8, 10]
        second_total = [1, 3]
        # Check coords and areas only
        expected_from_labels = pd.DataFrame(
            np.array([areas, x_centroids, y_centroids]).T,
            columns=['area', 'x_centroid', 'y_centroid'],
            index=pd.Index(labels, name='label'))
        pdt.assert_frame_equal(
            segmentation.extract_cell_dataframe(cell_labels),
            expected_from_labels)
        # Check mode 'total'
        expected_from_total = pd.DataFrame(
            np.array([first_total, second_total]).T,
            columns=['1', '2'], index=pd.Index(labels, name='label'))
        pdt.assert_frame_equal(
            segmentation.extract_cell_dataframe(cell_labels, image),
            pd.concat((expected_from_labels, expected_from_total), axis=1))
        # Check mode 'quadrant'
        quads = []
        for label in labels:
            inds = np.nonzero(cell_labels == label)
            quads.append(segmentation._quadrant_mean(inds, image))
        expected_from_quadrants = pd.DataFrame(
            np.array(quads),
            columns=['1', '2'], index=pd.Index(labels, name='label'))
        pdt.assert_frame_equal(
            segmentation.extract_cell_dataframe(
                cell_labels, image, mode='quadrant'),
            pd.concat((expected_from_labels, expected_from_quadrants), axis=1))

    def test_replace_labeled_pixels(self):
        cell_labels = np.array([
            [0, 1, 1, 0],
            [1, 1, 3, 3],
            [0, 0, 3, 3],
            [0, 0, 3, 3]
        ])
        df = pd.DataFrame([
            [100, 0],
            [150, 25],
        ], columns=['dsDNA', 'CD45'], index=pd.Index([1, 3], name='label'))
        expected_data = np.stack((
            np.array([
                [0, 100, 100, 0],
                [100, 100, 150, 150],
                [0, 0, 150, 150],
                [0, 0, 150, 150]
            ]),
            np.array([
                [0, 0, 0, 0],
                [0, 0, 25, 25],
                [0, 0, 25, 25],
                [0, 0, 25, 25]
            ]),
        ), axis=2)
        self.assertEqual(
            segmentation.replace_labeled_pixels(cell_labels, df),
            mi.MibiImage(expected_data, ['dsDNA', 'CD45']))
        self.assertEqual(
            segmentation.replace_labeled_pixels(cell_labels, df,
                                                columns=['dsDNA']),
            mi.MibiImage(expected_data[:, :, [0]], ['dsDNA']))

    def test_filter_by_size(self):
        cell_labels = np.array([
            [0, 1, 1, 2],
            [1, 1, 3, 3],
            [4, 4, 3, 3],
            [0, 4, 3, 3]
        ])
        expected = np.array([
            [0, 1, 1, 0],
            [1, 1, 0, 0],
            [2, 2, 0, 0],
            [0, 2, 0, 0]
        ])
        df = segmentation.extract_cell_dataframe(expected)
        filtered_image, filtered_df = segmentation.filter_by_size(
            cell_labels, 3, 5)
        assert_array_equal(filtered_image, expected)
        pdt.assert_frame_equal(filtered_df, df)

    def test_expand_objects(self):
        labels = np.array([
            [0, 0, 1, 1, 0],
            [2, 2, 1, 1, 1],
            [2, 2, 0, 1, 0],
            [0, 2, 0, 0, 0],
            [0, 0, 0, 0, 0]
        ])
        expected_1 = np.array([
            [2, 2, 1, 1, 1],
            [2, 2, 1, 1, 1],
            [2, 2, 2, 1, 1],
            [2, 2, 2, 1, 0],
            [0, 2, 0, 0, 0]
        ])
        expected_2 = np.array([
            [2, 2, 1, 1, 1],
            [2, 2, 1, 1, 1],
            [2, 2, 2, 1, 1],
            [2, 2, 2, 1, 1],
            [2, 2, 2, 1, 0]
        ])
        assert_array_equal(segmentation.expand_objects(labels, 0), labels)
        assert_array_equal(segmentation.expand_objects(labels, 1), expected_1)
        assert_array_equal(segmentation.expand_objects(labels, 2), expected_2)

    def test_adjacency_matrix(self):
        cell_labels = np.array([
            [0, 1, 2, 2, 0],
            [1, 1, 3, 3, 3],
            [1, 1, 3, 3, 3],
            [0, 0, 3, 3, 3]
        ])
        expected = np.array([
            [0, 0, 0, 0],
            [4/5, 1, 1/5, 2/5],
            [2/2, 1/2, 1, 2/2],
            [5/8, 2/8, 2/8, 1]])

        assert_array_equal(segmentation.get_adjacency_matrix(cell_labels),
                           expected)



if __name__ == '__main__':
    unittest.main()
