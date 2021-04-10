"""Splits single-depth MIBI scans into pseudo Depth Profiles.

Copyright (C) 2021 Ionpath, Inc.  All rights reserved."""

# pylint: disable=too-many-branches

import argparse
import glob
import os
import shutil
import struct

import numpy as np
import tqdm

HEADER_SIZE = 12
HEADER_FORMAT = 'iii'
SAT_ENTRY_SIZE = 10
SAT_ENTRY_FORMAT = 'qH'
DATA_SIZE = 4
DATA_FORMAT = 'HH'


def divide(msdf_file, num_scans, path=None):
    """Creates a pseudo depth profile from a single Image.msdf file.

    Args:
        msdf_file: The string path to a local msdf file.
        num_scans: The integer number of pseudo-depths into which to divide
            this msdf file. This must be a divisor of the number of ToF
            cycles per pixel.
        path: The string path to the folder into which to write the output
            msdf files, which will follow the convention Depth0/Image.msdf,
            Depth1/Image.msdf, etc. If Depth<n>/Image.msdf files already
            exist in this location, they will be overwritten. If no path is
            specified, this will default to creating a folder named
            PseudoDepths in the same directory as the input msdf file.

    Returns:
        - cycles_per_pixel: The integer number of ToF cycles per pixel in the
            original data.
        - cycles_per_scan: The integer number of ToF cycles per each output
            pseudo-depth.

    Raises:
        ValueError: Raised if the msdf file is not >=6.3.4.0 with ToF cycle
            number encoded, or if the number of scans given is not a divisor
            of the number of cycles per scan.
    """
    # Explicitly remove existing depths because there could have been a previous
    # splitting with more depths than this time, in which case only overwriting
    # the new ones will still leave the old extras around.
    if path is None:
        path = os.path.join(os.path.dirname(msdf_file), 'PseudoDepths')
    old_depths = glob.glob(os.path.join(path, 'Depth*'))
    for depth in old_depths:
        shutil.rmtree(depth)
    handles = []
    for i in range(num_scans):
        folder = os.path.join(path, f'Depth{i}')
        os.makedirs(folder)
        handles.append(open(os.path.join(folder, 'Image.msdf'), 'wb'))

    try:
        with open(msdf_file, 'rb') as infile:
            header = infile.read(HEADER_SIZE)
            file_variant, _, num_spectra = struct.unpack(HEADER_FORMAT, header)
            try:
                assert file_variant == 1
            except AssertionError:
                raise ValueError('Invalid input Image.msdf file.')
            for handle in handles:
                handle.write(header)
            # Adding a dimension to the SAT for each psuedo-depth, since
            # splitting them up will require creating a new SAT for each.
            depth_sat = np.zeros((num_spectra, 2, num_scans), int)
            buffer = infile.read(SAT_ENTRY_SIZE * num_spectra)
            sat = np.array(
                [i for i in struct.iter_unpack(SAT_ENTRY_FORMAT, buffer)],
                int)
            # Skip after to after SAT in new files; will update it later.
            after_sat = infile.tell()
            for handle in handles:
                handle.seek(after_sat)

            # Get cycles per pixel to calculate cycles per pseudo-depth.
            pixel = np.fromfile(
                infile, count=2 * sat[0, 1], dtype=np.ushort)[1::2]
            cycles_per_pixel = np.count_nonzero(pixel)
            if not cycles_per_pixel:
                raise ValueError(
                    'Cycle start indicators were not found in this file. '
                    'Please confirm that this file was created by MiniSIMS '
                    '>=6.3.4.0 with the "Encode ToF Cycle Start" option '
                    'selected.')
            cycles_per_scan, remainder = np.divmod(cycles_per_pixel, num_scans)
            if remainder:
                raise ValueError(
                    'Splitting {0} cycles per pixel into {1} depths does not '
                    'result in equal division. Please choose a divisor of {0}.'
                    .format(cycles_per_pixel, cycles_per_scan)
                )
            infile.seek(sat[0, 0])

            # Iterate through pixels while writing counts to each pseudo-depth.
            for i in tqdm.tqdm(range(num_spectra)):
                depth_sat[i, 0, :] = [handle.tell() for handle in handles]
                # Nx2 array of bins and counts for this pixel
                pixel = np.fromfile(infile, count=2*sat[i, 1], dtype=np.ushort
                                   ).reshape((sat[i, 1], 2))
                # splits zero-events (cycle boundaries) into list of n
                idx = np.split(np.where(pixel[:, 1] == 0)[0], num_scans)
                # gets index of end of each pseudo-depth
                boundaries = [i[-1] + 1 for i in idx[:-1]]
                # splits array into list of sub-arrays using boundary indices
                depths = np.split(pixel, boundaries, axis=0)
                for j, depth in enumerate(depths):
                    handles[j].write(depth)
                    depth_sat[i, 1, j] = len(depth)

        # Go back and write the new SAT for each file now that we know how
        # many entries there are for each pixel in each new pseudo-depth.
        for h, handle in enumerate(handles):
            handle.seek(HEADER_SIZE)
            for i in range(num_spectra):
                handle.write(struct.pack(
                    SAT_ENTRY_FORMAT,
                    depth_sat[i, 0, h], depth_sat[i, 1, h]
                ))
    finally:
        for handle in handles:
            handle.close()

    return cycles_per_pixel, cycles_per_scan


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('msdf_file', help='Path to single-depth msdf file.')
    parser.add_argument('num_scans', help='Integer number of pseudo-depths '
                                          'to divide this file into.')
    parser.add_argument('--path', help='Path to output location. If not '
                                       'provided, defaults to a new folder '
                                       'named "PseudoDepths" at the same '
                                       'location as the input msdf file.')
    args = parser.parse_args()
    divide(args.msdf_file, int(args.num_scans), args.path)
