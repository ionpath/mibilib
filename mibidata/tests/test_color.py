"""Tests for mibidata.color"""

import unittest

import numpy as np
import numpy.testing as npt

from mibidata import color
from mibidata.mibi_image import MibiImage


RGB = np.array([[
    [1., 1., 1.],
    [0.5, 0.5, 0.5],
    [0., 0., 0.],
    [1., 0., 0.],
    [0.75, 0.75, 0.],
    [0., 0.5, 0.],
    [0.5, 1., 1.],
    [0.5, 0.5, 1.],
    [0.75, 0.25, 0.75],
    [0., 1., 0.],
    [0., 0., 1.],
    [0.25, 0.25, 0.25]
]]).reshape(3, 4, 3)


HSL = np.array([[
    [0., 0., 1.],
    [0., 0., 0.5],
    [0., 0., 0.],
    [0., 1., 0.5],
    [np.pi / 3, 1., 0.375],
    [2 * np.pi / 3, 1., 0.25],
    [np.pi, 1., 0.75],
    [4 * np.pi / 3, 1., 0.75],
    [5 * np.pi / 3, 0.5, 0.5],
    [2 * np.pi / 3., 1., 0.5],
    [4 * np.pi / 3., 1., 0.5],
    [0., 0., 0.25],
]]).reshape(3, 4, 3)


class TestColor(unittest.TestCase):

    def test_hsl2rgb_rainbow(self):
        npt.assert_array_almost_equal(color.hsl2rgb(HSL), RGB)

    def test_hsl2rgb_out_of_range(self):
        hsl = HSL.copy()
        hsl[:, :, 0] += np.pi / 2
        with self.assertRaises(ValueError):
            color.hsl2rgb(hsl)
        hsl[:, :, 0] -= np.pi / 2
        hsl[:, :, 1:] += 0.1
        with self.assertRaises(ValueError):
            color.hsl2rgb(hsl)
        with self.assertRaises(ValueError):
            color.hsl2rgb(HSL - 0.1)

    def test_composite_to_red_and_cyan(self):
        red = np.random.randint(0, 100, (10, 10), np.uint16)
        cyan = np.arange(100).reshape((10, 10)).astype(np.uint16)
        im = MibiImage(np.stack((red, cyan), axis=2), ['red', 'cyan'])
        screened = color.composite(im, {'Red': 'red', 'Cyan': 'cyan'}, gamma=1)
        expected_red = ((red / np.max(red)) * 255).astype(int)
        expected_green_blue = (cyan / np.max(cyan) * 255).astype(int)
        # Could be off by one after round tripping through this all this
        max_diff_red = np.max(np.abs(
            (screened[:, :, 0]).astype(int) - expected_red))
        self.assertTrue(max_diff_red <= 1)
        max_diff_green = np.max(np.abs(
            (screened[:, :, 1]).astype(int) - expected_green_blue))
        self.assertTrue(max_diff_green <= 1)
        max_diff_blue = np.max(np.abs(
            (screened[:, :, 2]).astype(int) - expected_green_blue))
        self.assertTrue(max_diff_blue <= 1)


if __name__ == '__main__':
    unittest.main()
