""" Common convenience functions used in mibidata module.

Copyright (C) 2021 Ionpath, Inc.  All rights reserved."""

import re
import functools
import numpy as np

DELIMITERS = {'/', '\\'}


def encode_strings(string_list, encoding='utf-8'):
    """Encodes each string in a list into a bytes object and returns a list
    of bytes objects. Useful function when writing and reading string lists
    which are not supported in pytables.

    Args:
        string_list: A list of strings to encode.
        encoding: Encoding to use, defaults to UTF-8.

    Returns:
        A list of bytes objects that have been encoded with the given encoding.
    """
    return [s.encode(encoding) for s in string_list]


def decode_strings(bytes_objects_list, encoding='utf-8'):
    """Decodes each bytes object in a list into a string and returns a list
    of strings. Useful function when writing and reading string lists which are
    not supported in pytables.

    Args:
        bytes_objects_list: A list of strings to encode.
        encoding: Encoding to use, defaults to UTF-8.

    Returns:
        A list of strings that have been decoded with the given encoding.
    """
    return [b.decode(encoding) for b in bytes_objects_list]


def natural_sort(l):
    """Sorts a list of strings in the way that humans expect, in place.

    For example, this would order *'Depth2'* before *'Depth11'*, whereas
    ``sort`` would place those in the opposite order.

    Args:
        l: A list of strings.
    """
    def _strtoint(s):
        try:
            return int(s)
        except ValueError:
            return s

    def _alphanum_key(s):
        """Converts a string into a list of string and number."""
        return [_strtoint(c) for c in re.split('([0-9]+)', s)]
    l.sort(key=_alphanum_key)


def sort_channel_names(l):
    """Sorts a list of string in place such that number only string are after
    all text strings and text strings with numbers are sorted alphabetically.

    ex: ['beta-tubulin', 'CD20', 'CD4', 'CD45', 'CD8', 'dsDNA', 'Keratin',
        '23', '97', '144', '150']

    Args:
        l: A list of strings.
    """

    def compare_items(x, y):
        """The return value is negative if x < y,
        zero if x == y and strictly positive if x > y
        """
        try:
            fx = float(x)
            try:
                fy = float(y)
                # x and y are both numbers
                if fx < fy:
                    return -1
                if fx > fy:
                    return 1
                return 0
            except ValueError:
                # x is a number, y is a non-number
                return 1
        except ValueError:
            try:
                fy = float(y)
                # y is a number, x is a non-number
                return -1
            except ValueError:
                # x and y are non-numbers, compare lower case
                x_lower = x.lower()
                y_lower = y.lower()
                if x_lower < y_lower:
                    return -1
                if x_lower > y_lower:
                    return 1
                return 0

    l.sort(key=functools.cmp_to_key(compare_items))


def format_for_filename(label):
    """Replaces delimiters and utf-8 encodes targets for use as filenames."""
    for char in set(label).intersection(DELIMITERS):
        label = label.replace(char, '-')
    return label


def car2pol(x, y, x_c=0, y_c=0, degrees=False):
    """Convert cartesian to polar coordinates w.r.t. a central point.
    Angle phi is returned in the range [0, 2 pi) rad. A flag can be activated
    to return phi angles in degrees.

    Args:
        x, y: arrays of coordinates to transform.
        x_c, y_c: numbers representing the coordinates of the center
            (origin of polar coordinates). Optional; default is (0, 0).
        degrees: flag to return phi angles in degrees instead of radians.
            Optional; default is False (i.e. radians).

    Returns:
        r, phi: arrays of transformed coordinates.
    """
    r = np.sqrt((x - x_c)**2 + (y - y_c)**2)
    phi = np.arctan2(y - y_c, x - x_c)
    # convert: (-pi, pi] --> [0, 2 pi)
    phi[phi[:] < 0] += 2.*np.pi
    if degrees:
        phi *= 180./np.pi

    return r, phi
