"""Combines a folder of single-channel TIFFs into a multiplexed MIBItiff.

Copyright (C) 2021 Ionpath, Inc.  All rights reserved."""

import argparse
import datetime
import os
import re

import numpy as np
from skimage import io as skio

from mibidata import mibi_image as mi, panels, runs, tiff


def _load_single_channel(file_name):
    array = skio.imread(file_name)
    if array.dtype not in (np.uint16, np.uint8):
        raise ValueError(
            f'Invalid dtype {array.dtype}; must be uint8 or uint16')

    if array.dtype == np.uint8:
        array = array.astype(np.uint16)
    return array


def _match_target_filename(filenames, target):
    """Finds the file whose name matches target, target.tif, or target.tiff"""
    pattern = re.compile(re.escape(target).lower() + r'\.tiff?$')
    matches = [f for f in filenames if re.match(pattern, f.lower())]
    try:
        assert len(matches) == 1
    except AssertionError as ae:
        raise ValueError(f'TIFF matching {target} not found') from ae
    return matches[0]


def merge_mibitiffs(input_folder, out=None):
    """Merges a folder of single-channel MIBItiff files into a single MIBItiff.

    Args:
        input_folder: Path to a folder containing MIBItiff files. While these
            files may be single-channel, they are assumed to have accurate and
            consistent MIBI metadata.
        out: Optionally, a path to a location for saving the combined TIFF. If
           not specified, defaults to 'combined.tiff' inside the input folder.
    """
    pattern = re.compile(r'.+\.tiff?$')
    paths = [
        os.path.join(input_folder, f) for f in os.listdir(input_folder)
        if re.match(pattern, f.lower())]
    merged = tiff.read(paths[0])
    for path in paths[1:]:
        image = tiff.read(path)
        merged.append(image)

    if out is None:
        out = os.path.join(input_folder, 'combined.tiff')
    tiff.write(out, merged, multichannel=True)


def create_mibitiffs(input_folder, run_path, point, panel_path, slide, size,
                     run_label=None, instrument=None, tissue=None,
                     aperture=None, out=None):
    """Combines single-channel TIFFs into a MIBItiff.

    The input TIFFs are not assumed to have any MIBI metadata. If they do, it
    is suggested to use the simpler :meth:`~merge_mibitiffs` instead.

    Args:
        input_folder: Path to a folder containing single-channel TIFFs.
        run_path: Path to a run xml.
        point: Point name of the image, e.g. Point1 or Point2. This should match
            the name of folder generated for the raw data as it is listed in the
            run xml file.
        panel_path: Path to a panel CSV.
        slide: The slide ID.
        size: The size of the FOV in microns, i.e. 500.
        run_label: Optional custom run label for the combined TIFF. If uploading
            the output to MIBItracker, the run label set here must match the
            label of the MIBItracker run. Defaults to the name of the run xml.
        instrument: Optionally, the instrument ID.
        tissue: Optionally, the name of tissue.
        aperture: Optionally, the name of the aperture or imaging preset.
        out: Optionally, a path to a location for saving the combined TIFF. If
           not specified, defaults to 'combined.tiff' inside the input folder.
        run_label: Optionally, a custom run label for the `run` property of the
            image.
    """
    panel_df = panels.read_csv(panel_path)
    panel_name, _ = os.path.splitext(os.path.basename(panel_path))
    tiff_files = os.listdir(input_folder)

    fovs, calibration = runs.parse_xml(run_path)
    point_number = int(point[5:])
    try:
        fov = fovs[point_number - 1] # point number is 1-based, not 0-based
    except IndexError as ie:
        raise IndexError(f'{point} not found in run xml.') from ie
    if fov['date']:
        run_date = datetime.datetime.strptime(
            fov['date'], '%Y-%m-%dT%H:%M:%S').date()
    else:
        run_date = datetime.datetime.now().date()

    image_data = []
    for i in panel_df.index:
        tiff_path = os.path.join(
            input_folder, _match_target_filename(tiff_files,
                                                 panel_df['Target'][i]))
        data = _load_single_channel(tiff_path)
        image_data.append(data)

    image_data = np.stack(image_data, axis=2)

    image = mi.MibiImage(image_data,
                         list(zip(panel_df['Mass'], panel_df['Target'])))

    image.size = int(size)
    image.coordinates = (fov['coordinates'])
    image.filename = fov['run']
    image.run = run_label if run_label else fov['run']
    image.version = tiff.SOFTWARE_VERSION
    image.instrument = instrument
    image.slide = slide
    image.dwell = fov['dwell']
    image.scans = fov['scans']
    image.aperture = aperture
    image.fov_name = fov['fov_name']
    image.folder = fov['folder']
    image.tissue = tissue
    image.panel = panel_name
    image.date = run_date
    image.mass_offset = calibration['MassOffset']
    image.mass_gain = calibration['MassGain']
    image.time_resolution = calibration['TimeResolution']

    if out is None:
        out = os.path.join(input_folder, 'combined.tiff')

    tiff.write(out, image, multichannel=True)


if __name__ == '__main__':

    description = ('Generates a single multiplexed MIBItiff from a folder '
                   'containing individual single-channel TIFFs without MIBI '
                   'metadata. Note that if the single-channel TIFFs already '
                   'have the MIBItiff metadata, then a much simpler way to '
                   'merge them is to use combine_tiffs.merge_mibitiffs '
                   'instead.')

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        'folder',
        help='Folder containing single-channel TIFF files with a .tif or '
             '.tiff extension.',
    )
    parser.add_argument(
        'run_xml', help='Path to a run XML file.'
    )
    parser.add_argument(
        'point', help='The point number in the run, e.g. Point1 or Point2. '
                      'This should match the name of folder generated for the '
                      'raw data as it is listed in the run xml file.'
    )
    parser.add_argument(
        'panel',
        help='Path to a CSV file containing panel information. The CSV file '
             'must contain columns named \'Mass\' and \'Target\', where the '
             'contents of the \'Target\' column matches the names of the '
             'single-channel TIFFs, i.e. the column contains \'CD45\' and '
             'there is a file named \'CD45.tif\' or \'CD45.tiff\'. A panel '
             'downloaded from the MibiTracker is a valid format assuming the '
             'single-channel TIFF files are named accordingly.',
    )
    parser.add_argument(
        'slide', help='The slide ID.'
    )
    parser.add_argument(
        'size', help='The size of the FOV in microns e.g. 500.'
    )
    parser.add_argument(
        '--run_label',
        help='Optional custom run label for the combined TIFF. If uploading '
             'the multiplexed MIBItiff file to MIBItracker, the run label set '
             'here must match the label of the MIBItracker run.'
    )
    parser.add_argument(
        '--instrument', help='The instrument ID.'
    )
    parser.add_argument(
        '--tissue', help='The tissue type.'
    )
    parser.add_argument(
        '--aperture', help='The aperture or imaging preset used.'
    )
    parser.add_argument(
        '--out',
        help='Optional path to a location for the combined TIFF. If not '
             'specified, defaults to \'combined.tiff\' inside the '
             'input folder.',
    )
    args = parser.parse_args()
    create_mibitiffs(args.folder, args.run_xml, args.point, args.panel,
                     args.slide, args.size, run_label=args.run_label,
                     instrument=args.instrument, tissue=args.tissue,
                     aperture=args.aperture, out=args.out)
