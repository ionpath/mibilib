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
        image = mi.MibiImage(data, ['1', '2'])
        assert_array_equal(
            segmentation._circular_sectors_mean(inds,
                                                image,
                                                num_sectors=4),
            expected
        )


    def test_circular_sectors(self):
        """Test circular sectors method in segmentation.
        """
        # create data for image 2 channels
        channels = ['ch0', 'ch1']
        data = np.stack((
            # channel 0
            np.arange(36, dtype='float').reshape(6, 6),
            # this is the matrix:
            #np.array([[ 0,  1,  2,  3,  4,  5],
            #          [ 6,  7,  8,  9, 10, 11],
            #          [12, 13, 14, 15, 16, 17],
            #          [18, 19, 20, 21, 22, 23],
            #          [24, 25, 26, 27, 28, 29],
            #          [30, 31, 32, 33, 34, 35]], dtype='float')
            # channel 1
            np.array([
                [0, 0, 0, 0, 0, 0],
                [0, 1, 0, 0, 0, 0],
                [0, 0, 0, 1, 0, 0],
                [0, 0, 0, 0, 0, 1],
                [0, 1, 0, 0, 0, 0],
                [0, 0, 3, 0, 0, 2]], dtype='float'),
            ), axis=2)
        # assume labels are for cell ID 1, such as with label image:
        # np.array([
        #     [1, 1, 1, 1, 1, 0],
        #     [1, 1, 1, 1, 1, 0],
        #     [1, 1, 1, 1, 1, 0],
        #     [1, 1, 1, 1, 1, 0],
        #     [1, 1, 1, 1, 1, 0],
        #     [0, 0, 0, 0, 0, 0]])
        # indices of the pixels of the cell
        x = np.arange(5)
        y = x
        x_inds, y_inds = np.meshgrid(x, y, indexing='ij')
        inds = (y_inds.flatten(), x_inds.flatten())
        # sum within sectors and calculate geometric mean for each channel
        secs = []
        for i in range(len(channels)):
            sec1 = data[2][2][i] + data[2][3][i] + data[2][4][i] + data[3][4][i]
            sec2 = data[3][3][i] + data[4][3][i] + data[4][4][i]
            sec3 = data[3][2][i] + data[4][2][i] + data[4][1][i]
            sec4 = data[3][1][i] + data[4][0][i] + data[3][0][i]
            sec5 = data[2][1][i] + data[2][0][i] + data[1][0][i]
            sec6 = data[1][1][i] + data[0][0][i] + data[0][1][i]
            sec7 = data[1][2][i] + data[0][2][i] + data[0][3][i]
            sec8 = data[1][3][i] + data[0][4][i] + data[1][4][i]
            secs_geom_mean = np.power(sec1 * sec2 * sec3 * sec4 * \
                                sec5 * sec6 * sec7 * sec8, 1/8)
            secs.append(secs_geom_mean)
        expected = np.array(secs)
        # test the function
        image = mi.MibiImage(data, channels)
        circ_secs = segmentation._circular_sectors_mean(inds,
                                                        image,
                                                        num_sectors=8)
        assert_array_equal(circ_secs, expected)


    def test_circular_sectors_small_cell(self):
        """Test small cell with empty sectors.
        """
        # create data for image 2 channels
        channels = ['ch0', 'ch1']
        data = np.stack((
            # channel 0
            np.arange(16, dtype='float').reshape(4, 4),
            # this is the matrix:
            #np.array([[ 0,  1,  2,  3],
            #          [ 4,  5,  6,  7],
            #          [ 8,  9, 10, 11],
            #          [12, 13, 14, 15]], dtype='float')
            # channel 1
            np.array([
                [0, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 0, 1],
                [0, 0, 0, 0]], dtype='float'),
            ), axis=2)
        # assume labels are for cell ID 1, such as with label image:
        # np.array([
        #     [0, 1, 1, 0],
        #     [0, 1, 1, 0],
        #     [0, 0, 0, 0],
        #     [0, 0, 0, 0]])
        # indices of the pixels of the cell
        inds = ((0, 0, 1, 1), (1, 2, 1, 2))
        # sum within sectors and calculate geometric mean for each channel
        secs = []
        for i in range(len(channels)):
            sec1 = 1 # empty sector
            sec2 = data[1][2][i]
            sec3 = 1 # empty sector
            sec4 = data[1][1][i]
            sec5 = 1 # empty sector
            sec6 = data[0][1][i]
            sec7 = 1 # empty sector
            sec8 = data[0][2][i]
            secs_geom_mean = np.power(sec1 * sec2 * sec3 * sec4 * \
                                sec5 * sec6 * sec7 * sec8, 1/8)
            secs.append(secs_geom_mean)
        expected = np.array(secs)
        # test the function
        image = mi.MibiImage(data, channels)
        circ_secs = segmentation._circular_sectors_mean(inds,
                                                        image,
                                                        num_sectors=8)
        assert_array_equal(circ_secs, expected)


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
            quads.append(segmentation._circular_sectors_mean(inds,
                                                             image,
                                                             num_sectors=4))
        expected_from_quadrants = pd.DataFrame(
            np.array(quads),
            columns=['1', '2'], index=pd.Index(labels, name='label'))
        pdt.assert_frame_equal(
            segmentation.extract_cell_dataframe(
                cell_labels, image, mode='quadrant'),
            pd.concat((expected_from_labels, expected_from_quadrants), axis=1))
        # Check mode 'circular_sectors'
        secs = []
        for label in labels:
            inds = np.nonzero(cell_labels == label)
            num_sectors = 8
            secs.append(segmentation._circular_sectors_mean(inds, image,
                                                            num_sectors))
        expected_from_circular_sectors = pd.DataFrame(
            np.array(secs),
            columns=['1', '2'], index=pd.Index(labels, name='label'))
        pdt.assert_frame_equal(
            segmentation.extract_cell_dataframe(
                cell_labels, image, mode='circular_sectors',
                num_sectors=num_sectors),
            pd.concat((expected_from_labels, expected_from_circular_sectors),
                      axis=1))


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
