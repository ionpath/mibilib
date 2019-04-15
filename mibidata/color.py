import numpy as np

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
# Defines the minimum number of counts to scale images in
# `composite`. This intended to prevent images with
# only a few counts from being scaled to [0, 1].
MIN_COUNTS_FOR_SCALING = 10


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


def composite(image, color_map, gamma=1/3):
    """Combines multiple image channels by color into a 3-D array.

    Args:
        image: A MibiImage/
        color_map: A dictionary keyed by color with values of channel names
            corresponding to a subset of those in the MibiImage. The
            allowed colors are 'Cyan', 'Yellow', 'Magenta', 'Green',
            'Orange', 'Violet', 'Red' and 'Blue'.
        gamma: The value with which to scale the image data. Defaults to 1/3.
            If no gamma correction is desired, set to 1.

    Returns:
        An NxMx3 uint8 array of an RGB image.
    """
    data_map = {}
    for key, val in color_map.items():
        data_map[key] = np.power(
            image[val] / np.maximum(np.max(image[val]), MIN_COUNTS_FOR_SCALING),
            gamma)
    screened = _screen(data_map)
    return np.uint8(screened * 255)
