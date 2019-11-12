"""Color transformation and composites.

Copyright (C) 2019 Ionpath, Inc.  All rights reserved."""

import numpy as np
from scipy import ndimage

COLORS = {
    'Cyan': np.pi,
    'Yellow': np.pi / 3,
    'Magenta': 5 * np.pi / 3,
    'Green': 2 * np.pi / 3,
    'Orange': 0.2166 * np.pi,
    'Violet': 1.483 * np.pi,
    'Red': 0,
    'Blue': 4 * np.pi / 3,
}


def _trim(array, lower=0., upper=1.):
    """Trims an array to a specified range; used for floating point errors."""
    return np.minimum(np.maximum(array, lower), upper)


def rgb2hsl(rgb):
    """Converts an RGB array to HSL.

    The hue is scaled to [0, 2*pi]; the saturation and lightness to [0, 1].

    Args:
        rgb: An NxMx3 array of floats in the unit interval.

    Returns:
        An array the same shape as rgb converted to HSL coordinates.

    Raises:
        ValueError: Raised if the input array has values outside of the unit
            interval.

    References:
        HSL_and_HSV. Wikipedia: The Free Encyclopedia. Accessed 09/11/2016.
            http://en.wikipedia.org/wiki/HSL_and_HSV.
    """
    if not (np.all(rgb >= 0.) and np.all(rgb <= 1.)):
        raise ValueError('Input array must have values in the unit interval.')

    max_channel = np.max(rgb, axis=2)
    min_channel = np.min(rgb, axis=2)
    channel_range = max_channel - min_channel

    # Use polar coordinate conversion rather than hexagons.
    alpha = (2 * rgb[:, :, 0] - rgb[:, :, 1] - rgb[:, :, 2]) / 2
    beta = np.sqrt(3) / 2 * (rgb[:, :, 1] - rgb[:, :, 2])
    hue = np.arctan2(beta, alpha)
    # Shift from [-pi, pi] to [0, 2*pi]
    hue[hue < 0] += 2 * np.pi

    luminosity = (max_channel + min_channel) / 2

    saturation = np.zeros_like(channel_range)
    denom = (1 - np.abs(2 * luminosity - 1))
    # Set the saturation to zero along the grayscale.
    idx = np.logical_and(channel_range > 0, ~np.isclose(denom, 0)) # pylint: disable=assignment-from-no-return
    saturation[idx] = channel_range[idx] / (
        1 - np.abs(2 * luminosity[idx] - 1))

    return np.stack((_trim(hue, upper=2 * np.pi),
                     _trim(saturation),
                     _trim(luminosity)), axis=2)


def hsl2rgb(hsl):
    """Converts an HSL array to RGB.

    Args:
        hsl: An NxMx3 array of floats representing an HSL image. The H layer
            must have values in the range [0, 2*pi]; the S and L layers must
            have values in the unit interval.

    Returns:
        An array the same shape as hsl converted to RGB coordinates.

    Raises:
        ValueError: Raised if the input array has values outside of the
            expected intervals.

    References:
        HSL_and_HSV. Wikipedia: The Free Encyclopedia. Accessed 09/11/2016.
            http://en.wikipedia.org/wiki/HSL_and_HSV.
    """
    if np.any(hsl < 0.):
        raise ValueError('Input array must have values with hue in the '
                         'interval [0, 2*pi] and saturation and luminosity in '
                         'the interval [0, 1], but this array has minimum %s.'
                         % hsl.min())
    if np.any(hsl[:, :, 1:] > 1.):
        raise ValueError('Input array must have values of saturation and '
                         'luminosity in the interval [0, 1], but this array '
                         'has maximum saturation and luminosity of %s.'
                         % hsl[:, :, 1:].max())
    if np.any(hsl[:, :, 0] > 2 * np.pi):
        raise ValueError('Input array must have values with hue in the '
                         'interval [0, 2*pi] and saturation and luminosity in '
                         'the interval [0, 1], but this array has maximum '
                         'hue of %s.' % hsl[:, :, 0].max())

    chroma = (1 - np.abs(2 * hsl[:, :, 2] - 1)) * hsl[:, :, 1]
    # H is in [0, 2*pi], thus Hprime is in [0, 6]
    hue_prime = 3 * hsl[:, :, 0] / np.pi
    x = chroma * (1 - np.abs(np.mod(hue_prime, 2) - 1))
    # assign bin 1-6 for hue_prime where bin i is [i-1, i]
    sector = np.digitize(hue_prime, range(7))
    cxz = np.stack((chroma, x, np.zeros_like(x)), axis=2)
    rgb = np.zeros_like(hsl)

    def rgb_sector(ind, order):
        idx = sector == ind
        ar = cxz[:, :, order]
        rgb[idx, :] = ar[idx, :]

    rgb_sector(1, [0, 1, 2])
    rgb_sector(2, [1, 0, 2])
    rgb_sector(3, [2, 0, 1])
    rgb_sector(4, [2, 1, 0])
    rgb_sector(5, [1, 2, 0])
    rgb_sector(6, [0, 2, 1])

    match_value = hsl[:, :, 2] - chroma / 2
    for i in range(3):
        rgb[:, :, i] += match_value
    np.clip(rgb, 0., 1., out=rgb)

    return rgb


def rgb2cym(rgb):
    """Converts an RGB array to CYM.

    Args:
        rgb: An NxMx3 array of floats in the unit interval.

    Returns:
        An array the same shape as rgb converted to CYM colors.
    """
    return invert_luminosity(1 - rgb[:, :, [0, 2, 1]])


def invert_luminosity(rgb):
    """Inverts the luminosity of an RGB image.

    Args:
        rgb: An NxMx3 array of floats in the unit interval.

    Returns:
        An array the same shape as rgb that has had its luminosity inverted.
    """
    hsl = rgb2hsl(rgb)
    hsl[:, :, 2] = 1 - hsl[:, :, 2]
    return hsl2rgb(hsl)


def _gray2hsl(array, angle):
    """Converts NxN grayscale to RGB of a single color.

    The input array is assumed to be scaled in the unit interval [0, 1]
    The angle is in the range [0, 2*pi]
    """
    hsl = np.zeros((array.shape[0], array.shape[1], 3))
    hsl[:, :, 0] = angle
    hsl[array > 0, 1] = 1
    hsl[:, :, 2] = array / 2
    return hsl


def _porter_duff_screen(backdrop, source):
    """Reference: https://www.w3.org/TR/compositing-1/#blendingscreen"""
    return backdrop + source - (backdrop * source)


def _screen(color_map):
    """Combines multiple image channels by color into a 3-D array.

    Args:
        A map keyed by color with values of NxM arrays that will be assigned
        that hue before screening with the others. The allowed colors are
        'Cyan', 'Yellow', 'Magenta', 'Green', 'Orange', 'Violet', 'Red' and
        'Blue'. The arrays must contain floats in the unit interval.

    Returns:
        An NxMx3 float array of an RGB image with values in the unit interval.
    """
    screened = None
    for color, array in color_map.items():
        hsl = _gray2hsl(array, COLORS[color])
        rgb = hsl2rgb(hsl)
        if screened is None:
            screened = rgb
        else:
            screened = _porter_duff_screen(screened, rgb)
    return screened


def composite(image, color_map, gamma=1/3, min_scaling=10):
    """Combines multiple image channels by color into a 3-D array.

    Args:
        image: A MibiImage.
        color_map: A dictionary keyed by color with values of channel names
            corresponding to a subset of those in the MibiImage. The
            allowed colors are 'Cyan', 'Yellow', 'Magenta', 'Green',
            'Orange', 'Violet', 'Red' and 'Blue'.
        gamma: The value with which to scale the image data. Defaults to 1/3.
            If no gamma correction is desired, set to 1.
        min_scaling: The minimum number of counts used as the divisor for each
            channel before applying gamma. This intended to prevent images with
            only a few counts from being scaled incorrectly to [0, 1].

    Returns:
        An NxMx3 uint8 array of an RGB image.
    """
    data_map = {}
    for key, val in color_map.items():
        data_map[key] = np.power(  # pylint: disable=assignment-from-no-return
            image[val] / np.maximum(np.max(image[val]), min_scaling),
            gamma)
    screened = _screen(data_map)
    return np.uint8(screened * 255)


def gray2hsl(array, angle):
    """Converts NxN grayscale to RGB of a single color.

    The input array is assumed to be scaled in the unit interval [0, 1]
    The angle is in the range [0, 2*pi]
    """
    hsl = np.zeros((array.shape[0], array.shape[1], 3))
    hsl[:, :, 0] = angle
    hsl[array > 0, 1] = 1
    hsl[:, :, 2] = array / 2
    return hsl


def compose_overlay_from_image_data(image, overlay_settings):
    """Overlays multiple image channels using overlay_settings from mibitracker.

    Args:
        image: A MibiImage.
        overlay_settings: Color overlay dictionary with the following fields:
            'brightness': float between -1 and 1.
            'channel': Name of the MibiImage channel.
            'color': One of the following: 'Cyan', 'Yellow', 'Magenta', 'Green',
                'Orange', 'Violet', 'Red', 'Blue', or 'Gray'.
            'intensity_higher': Upper limit of the channel intensity.
            'intensity_lower': Lower limit of the channel intensity.

    Returns:
        An NxMx3 uint8 array of an RGB image.
    """
    # Convolve with this filter no matter what, to mimic browser rendering.
    kernel = np.array([
        [0.05, 0.1, 0.05],
        [0.1, 0.4, 0.1],
        [0.05, 0.1, 0.05]
    ])
    for i, item in enumerate(overlay_settings):
        int_array = image[item['channel']]
        # Because we treat the min differently, don't use np.clip
        range_min, range_max = item['intensity_lower'], item['intensity_higher']
        int_array[int_array > range_max] = range_max
        int_array[int_array < range_min] = 0
        float_array = int_array / float(range_max)
        float_array[int_array > 0] += item['brightness']
        # Apply default filter even if no blurring
        ndimage.filters.convolve(float_array, kernel, output=float_array)
        if item['blur'] > 0:
            ndimage.filters.gaussian_filter(
                float_array, item['blur'] * 100, output=float_array)
        np.clip(float_array, 0, 1, out=float_array)
        if item['color'] == 'Gray':
            rgb = np.stack((float_array, float_array, float_array), axis=2)
        else:
            hsl = gray2hsl(float_array, COLORS[item['color']])
            rgb = hsl2rgb(hsl)
        if i == 0:
            overlay = rgb
        else:
            overlay = _porter_duff_screen(composite, rgb)
    return np.uint8(overlay * 255)
