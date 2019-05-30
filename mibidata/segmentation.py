"""Utilities for working with segmentation data.

Copyright (C) 2019 Ionpath, Inc.  All rights reserved."""

import numpy as np
import pandas as pd
from scipy import ndimage as ndi

from mibidata import mibi_image as mi


def extract_cell_dataframe(label_image, image=None, mode='total'):
    """Creates a dataframe of single-cell statistics from a labeled image.

    Args:
        label_image: An NxM array where each pixel's nonnegative integer value
            corresponds to the label of an image region, such as a cell or
            other segment.
        image: Optionally, a MibiImage of an NxM field of view. Defaults to
            None; if not None, the sum or score (depending on the mode) of each
            channel within each labeled region is returned as column of the
            dataframe. Otherwise, only the regions' size and area are returned.
        mode: One of``'total'`` or ``'quadrant'``, defaulting to ``'total'``. If
            ``'total'`, the ion counts within each labeled region are summed. If
            ``quadrant``, the geometric mean of each regions's four quadrants
            is calculated, which favors regions with even spatial distribution.
            This mode is ignored if an image is not specified.

    Returns:
        A dataframe indexed by image region's label, and whose columns
        include the area, centroid, and if included the total or scored
        counts of the image's channels within each region.
    """
    segment_labels = np.unique(label_image)
    segment_labels = segment_labels[segment_labels > 0]

    columns = ['label', 'area', 'x_centroid', 'y_centroid']
    if image is not None:
        columns += list(image.targets or image.channels)

    rows = []
    for segment_label in segment_labels:
        region = label_image == segment_label
        nonzeros = np.nonzero(region)

        row = [segment_label, len(nonzeros[0]), int(round(nonzeros[1].mean())),
               int(round(nonzeros[0].mean()))]
        if image is not None:
            if mode == 'total':
                vals = image.data[nonzeros[0], nonzeros[1], :].sum(axis=0)
            elif mode == 'quadrant':
                vals = _quadrant_mean(nonzeros, image)
            else:
                raise ValueError('"mode" must be either "total" or "quadrant"')
            row.extend(vals)
        rows.append(row)
    return pd.DataFrame(rows, columns=columns).set_index('label')


def _quadrant_mean(inds, image):
    """Gets the geometric mean of a regions's intensities across its quadrants.

    Args:
        inds: A tuple of 2 arrays of the y- and x- indices of the pixels in a
            segmented region of an image.
        image: A MibiImage in which the corresponding pixel indices are located.

    Returns:
        An array whose length is equal to the number of channels in the image.
        Each value in the array is the geometric mean of the image's integrated
        channel intensities over the regions's four quadrants.
    """
    y_center, x_center = np.mean(inds, axis=1)
    vals = image.data[inds]  # has shape (num_pixels_in_cell, num_channels)
    upper_left = vals[(inds[0] <= y_center) & (inds[1] < x_center)].sum(axis=0)
    upper_right = vals[(inds[0] < y_center) & (inds[1] >= x_center)].sum(axis=0)
    lower_left = vals[(inds[0] > y_center) & (inds[1] <= x_center)].sum(axis=0)
    lower_right = vals[(inds[0] >= y_center) & (inds[1] > x_center)].sum(axis=0)
    quads = np.stack((upper_left, upper_right, lower_left, lower_right), axis=1)
    return np.power(np.product(quads, axis=1), 1 / 4)


def replace_labeled_pixels(label_image, df, columns=None):
    """Replaces the pixels within each label with a value from a dataframe.

    Args:
        label_image: An NxM array where each pixel's nonnegative integer value
            corresponds to the label of an image region, such as a cell or
            other segment.
        df: A dataframe whose index corresponds to the integers in the
            label_array, and whose column values will replace the labels in the
            returned image.
        columns: An optional sequence of which columns from the dataframe to
            include in the returned image. Defaults to None, which uses all
            columns in the dataframe.

    Returns:
        A :class:`mibitof.mibi_image.MibiImage` instance where each channel
        corresponds to a dataframe column, and the data is a copy of the label
        image where each pixel has been replaced with the corresponding value
        from that label's row in the dataframe.
    """
    if columns is None:
        columns = df.columns
    label_array = np.zeros((label_image.max() + 1, len(columns)),
                           dtype=label_image.dtype)
    label_array[df.index, :] = df[columns]
    columns = [str(i) for i in columns]
    return mi.MibiImage(label_array[label_image], columns)


def expand_objects(label_image, distance):
    """Expands labeled objects in an image by a given number of pixels.

    Args:
        label_image: An NxM array where each pixel's nonnegative integer value
            corresponds to the label of an image region, such as a cell or
            other segment.
        distance: The distance (in pixels) to expand each object.

    Returns:
        A new label array of the expanded objects.
    """
    background = label_image == 0
    distances, (i, j) = ndi.distance_transform_edt(background,
                                                   return_indices=True)
    new_labels = label_image.copy()

    # This creates a mask for the pixels we will expand into, and then
    # sets them to the label of the closet non-background pixel.
    mask = background & (distances <= distance)
    new_labels[mask] = label_image[i[mask], j[mask]]
    return new_labels


def filter_by_size(label_image, min_size, max_size):
    """Removes segments outside of a specified size range.

    Args:
        label_image: An NxM array where each pixel's nonnegative integer value
            corresponds to the label of an image region, such as a cell or
            other segment.
        min_size: The minimum area in pixels of a segment.
        max_size: The maximum area in pixels of a segment.

    Returns:
        A new label image, where segments outside of the size range have been
        set to zero, and a dataframe of its labels, centroids and area.
    """
    df = extract_cell_dataframe(label_image)
    segment_labels = df.index[(df['area'] >= min_size) &
                              (df['area'] <= max_size)]
    new_labels = list(range(1, len(segment_labels) + 1))
    new_image = replace_labeled_pixels(
        label_image, pd.DataFrame(new_labels, index=segment_labels))
    new_df = pd.DataFrame(df.loc[segment_labels, :]).set_index(
        pd.Index(new_labels, name='label'))
    return np.squeeze(new_image.data), new_df


def get_adjacency_matrix(label_image):
    """Calculates adjacency matrix.

    Args:
        label_image: An NxM array where each pixel's nonnegative integer value
            corresponds to the label of an image region, such as a cell or
            other segment.
            
    Returns:
        adjacency_matrix: NxN array of floats (N is the number of labels)
            Each i, j element of the adjacency_matrix corresponds to the 
            fraction of the i region boundary length that is shared with j 
            region. 
    
    """

    # To find the adjacent regions we stack nearest neighbors of label_image
    # and look for pixles with more than 1 label on the stack

    # To create the stack we first need to pad label_image with zeros
    pad_image = np.pad(label_image, 1, 'constant').astype(int)
    label_stack = np.array([
        pad_image[:-2, 1:-1],
        pad_image[1:-1, :-2], pad_image[1:-1, 1:-1], pad_image[1:-1, 2:],
        pad_image[2:, 1:-1],
    ])
    # next we sort labels along the stack
    label_stack = np.sort(label_stack, 0)
    # we find duplicate labels
    duplicates = label_stack[1:, :, :] == label_stack[:-1, :, :]
    # and set duplicates values to -1
    label_stack[1:, :, :][duplicates] = -1

    # We can now create an image of labeled region boundaries
    labeled_boundaries = ((label_stack > -1).sum(0) > 1) * label_image

    # Finally we create the adjacency_matrix
    number_of_labels = label_image.max()
    adjacency_matrix = np.zeros([number_of_labels + 1] * 2)
    for label_i in range(1, number_of_labels+1):
        boundary = labeled_boundaries == label_i
        boundary_labels = label_stack[:, boundary]
        label_j, label_count = np.unique(
            boundary_labels[boundary_labels != -1],
            return_counts=True)
        print(label_i,label_j, label_count, boundary.sum())
        adjacency_matrix[label_i, label_j] = label_count / boundary.sum()

    return adjacency_matrix
