"""Read and write to and from IONpath MIBItiff files.

Copyright (C) 2019 Ionpath, Inc.  All rights reserved."""

import collections
from fractions import Fraction
import datetime
import json
import os

import numpy as np
from skimage.external.tifffile import TiffFile, TiffWriter

from mibidata import mibi_image as mi, util

# Increment this when making functional changes.
SOFTWARE_VERSION = 'IonpathMIBIv1.0'
# Coordinates of where the slide labels are within the optical image.
_TOP_LABEL_COORDINATES = ((570, 1170), (355, 955))
_BOTTOM_LABEL_COORDINATES = ((1420, 2020), (355, 955))
# Datetime format saved by TiffFile
_DATETIME_FORMAT = '%Y:%m:%d %H:%M:%S'
# Conversion factor from micron to cm
_MICRONS_PER_CM = 10000
# Max denominator for rational arguments in tifffile.py
_MAX_DENOMINATOR = 1000000
# Encoding of tiff tags.
ENCODING = 'utf-8'


def _micron_to_cm(arg):
    """Converts microns (1cm = 1e4 microns) to a fraction tuple in cm."""
    frac = Fraction(float(arg) / _MICRONS_PER_CM).limit_denominator(
        _MAX_DENOMINATOR)
    return frac.numerator, frac.denominator


def _cm_to_micron(arg):
    """Converts cm fraction to microns (1cm = 1e4 microns)."""
    return float(arg[0]) / float(arg[1]) * _MICRONS_PER_CM


# pylint: disable=too-many-branches,too-many-statements
def write(filename, image, sed=None, optical=None, ranges=None,
          multichannel=True, write_float=False):
    """Writes MIBI data to a multipage TIFF.

    Args:
        filename: The path to the target file if multi-channel, or the path to
            a folder if single-channel.
        image: A ``mibitof.mibi_image.MibiImage`` instance.
        sed: Optional, an array of the SED image data. This is assumed to be
            grayscale even if 3-dimensional, in which case only one channel
            will be used.
        optical: Optional, an RGB array of the optical image data.
        ranges: A list of (min, max) tuples the same length as the number of
            channels. If None, the min will default to zero and the max to the
            max pixel value in that channel. This is used by some external
            software to calibrate the display.
        multichannel: Boolean for whether to create a single multi-channel TIFF,
            or a folder of single-channel TIFFs. Defaults to True; if False,
            the sed and optical options are ignored.
        write_float: If True, saves the image data as float32 values (for
            opening properly in certain software such as Halo). Defaults to
            False which will save the image data as uint16. Note: setting
            write_float to True does not normalize or scale the data before
            saving, however saves the integer counts as floating point numbers.

    Raises:
        ValueError: Raised if the image is not a
            ``mibitof.mibi_image.MibiImage`` instance, or if its coordinates
            run date, or size are None.
    """
    if not isinstance(image, mi.MibiImage):
        raise ValueError('image must be a mibitof.mibi_image.MibiImage '
                         'instance.')
    if image.coordinates is None or image.size is None:
        raise ValueError('Image coordinates and size must not be None.')
    if image.masses is None or image.targets is None:
        raise ValueError('Image channels must contain both masses and targets.')
    if np.issubdtype(image.data.dtype, np.integer) and not write_float:
        range_dtype = 'I'
    else:
        range_dtype = 'd'
    if ranges is None:
        ranges = [(0, m) for m in image.data.max(axis=(0, 1))]

    coordinates = [
        (286, '2i', 1, _micron_to_cm(image.coordinates[0])),  # x-position
        (287, '2i', 1, _micron_to_cm(image.coordinates[1])),  # y-position
    ]
    resolution = (image.data.shape[0] * 1e4 / float(image.size),
                  image.data.shape[1] * 1e4 / float(image.size),
                  'cm')

    metadata = {
        'mibi.run': getattr(image, 'run'),
        'mibi.version': getattr(image, 'version'),
        'mibi.instrument': getattr(image, 'instrument') or 'MIBI',
        'mibi.slide': getattr(image, 'slide'),
        'mibi.dwell': getattr(image, 'dwell'),
        'mibi.scans': getattr(image, 'scans'),
        'mibi.aperture': getattr(image, 'aperture'),
        'mibi.fov_id': getattr(image, 'fov_id'),
        'mibi.fov_name': getattr(image, 'fov_name'),
        'mibi.folder': getattr(image, 'folder'),
        'mibi.tissue': getattr(image, 'tissue'),
        'mibi.panel': getattr(image, 'panel'),
        'mibi.mass_offset': getattr(image, 'mass_offset'),
        'mibi.mass_gain': getattr(image, 'mass_gain'),
        'mibi.time_resolution': getattr(image, 'time_resolution'),
        'mibi.miscalibrated': getattr(image, 'miscalibrated'),
        'mibi.check_reg': getattr(image, 'check_reg'),
        'mibi.filename': getattr(image, 'filename'),
        'mibi.description': getattr(image, 'description'),
        'mibi.optional_metadata': getattr(image, 'optional_metadata')
    }
    description = {
        key: val for key, val in metadata.items() if val is not None}

    if multichannel:
        targets = list(image.targets)
        util.sort_channel_names(targets)
        indices = image.channel_inds(targets)
        with TiffWriter(filename, software=SOFTWARE_VERSION) as infile:
            for i in indices:
                metadata = description.copy()
                metadata.update({
                    'image.type': 'SIMS',
                    'channel.mass': int(image.masses[i]),
                    'channel.target': image.targets[i],
                })
                page_name = (
                    285, 's', 0, '{} ({})'.format(image.targets[i],
                                                  image.masses[i])
                )
                min_value = (340, range_dtype, 1, ranges[i][0])
                max_value = (341, range_dtype, 1, ranges[i][1])
                page_tags = coordinates + [page_name, min_value, max_value]

                if write_float:
                    to_save = image.data[:, :, i].astype(np.float32)
                else:
                    to_save = image.data[:, :, i]

                infile.save(
                    to_save, compress=6, resolution=resolution,
                    extratags=page_tags, metadata=metadata, datetime=image.date)
            if sed is not None:
                if sed.ndim > 2:
                    sed = sed[:, :, 0]

                sed_resolution = (sed.shape[0] * 1e4 / float(image.size),
                                  sed.shape[1] * 1e4 / float(image.size),
                                  'cm')

                page_name = (285, 's', 0, 'SED')
                page_tags = coordinates + [page_name]
                infile.save(sed, compress=6, resolution=sed_resolution,
                            extratags=page_tags, metadata={'image.type': 'SED'})
            if optical is not None:
                infile.save(optical, compress=6,
                            metadata={'image.type': 'Optical'})
                label_coordinates = (
                    _TOP_LABEL_COORDINATES if image.coordinates[1] > 0 else
                    _BOTTOM_LABEL_COORDINATES)
                slide_label = np.fliplr(np.moveaxis(
                    optical[label_coordinates[0][0]:label_coordinates[0][1],
                            label_coordinates[1][0]:label_coordinates[1][1]],
                    0, 1))
                infile.save(slide_label, compress=6,
                            metadata={'image.type': 'Label'})

    else:
        for i in range(image.data.shape[2]):
            metadata = description.copy()
            metadata.update({
                'image.type': 'SIMS',
                'channel.mass': int(image.masses[i]),
                'channel.target': image.targets[i],
            })
            page_name = (285, 's', 0, '{} ({})'.format(
                image.targets[i], image.masses[i]))
            min_value = (340, range_dtype, 1, ranges[i][0])
            max_value = (341, range_dtype, 1, ranges[i][1])
            page_tags = coordinates + [page_name, min_value, max_value]

            if write_float:
                target_filename = os.path.join(
                    filename, '{}.float.tiff'.format(
                        util.format_for_filename(image.targets[i])))
            else:
                target_filename = os.path.join(
                    filename, '{}.tiff'.format(
                        util.format_for_filename(image.targets[i])))

            with TiffWriter(target_filename,
                            software=SOFTWARE_VERSION) as infile:

                if write_float:
                    to_save = image.data[:, :, i].astype(np.float32)
                else:
                    to_save = image.data[:, :, i]

                infile.save(
                    to_save, compress=6, resolution=resolution,
                    metadata=metadata, datetime=image.date,
                    extratags=page_tags)


def read(file, sims=True, sed=False, optical=False, label=False):
    """Reads MIBI data from an IonpathMIBI TIFF file.

    Args:
        file: The string path or an open file object to a MIBItiff file.
        sims: Boolean for whether to return the SIMS (MIBI) data. Defaults to
            True.
        sed: Boolean for whether to return the SED data. Defaults to False.
        optical: Boolean for whether to return the optical image. Defaults to
            False.
        label: Boolean for whether to return the slide label image. Defauls to
            False.

    Returns: A tuple of the image types set to True in the parameters, in the
        order SIMS, SED, Optical, Label (but including only those types
        specified). The SIMS data will be returned as a
        ``mibitof.mibi_image.MibiImage`` instance; the other image types will be
        returned as numpy arrays. If an image type is selected to be returned
        but is not present in the image, it will be returned as None.

    Raises:
        ValueError: Raised if the input file is not of the IonpathMIBI
            format, or if no image type selected to be returned.
    """
    return_types = collections.OrderedDict([
        ('sims', sims), ('sed', sed), ('optical', optical), ('label', label)
    ])
    if not any((val for val in return_types.values())):
        raise ValueError('At least one image type must be specified to return.')
    to_return = {}
    metadata = {}
    sims_data = []
    channels = []
    with TiffFile(file) as tif:
        _check_software(tif)
        for page in tif.pages:
            description = _page_description(page)
            image_type = description['image.type'].lower()
            if sims and image_type == 'sims':
                channels.append((description['channel.mass'],
                                 description['channel.target']))
                sims_data.append(page.asarray())
                #  Get metadata on first SIMS page only
                if not metadata:
                    metadata.update(_page_metadata(page, description))
            elif return_types.get(image_type):
                to_return[image_type] = page.asarray()
    if sims:
        to_return['sims'] = mi.MibiImage(np.stack(sims_data, axis=2),
                                         channels, **metadata)
    return_vals = tuple(
        to_return.get(key)for key, val in return_types.items() if val)
    if len(return_vals) == 1:
        return return_vals[0]
    return return_vals


def _check_software(file):
    """Checks the software version of an open TIF file."""
    software = file.pages[0].tags.get('software')
    if not software or not software.value.decode(ENCODING).startswith(
            'IonpathMIBI'):
        raise ValueError('File is not of type IonpathMIBI.')


def _page_description(page):
    """Loads and decodes the JSON description in a TIF page."""
    return json.loads(
        page.tags['image_description'].value.decode(ENCODING))


def _page_metadata(page, description):
    """Parses the page metadata into a dictionary."""
    assert page.tags['resolution_unit'].value == 3
    x_resolution = page.tags['x_resolution'].value[0] / \
                   page.tags['x_resolution'].value[1]
    y_resolution = page.tags['y_resolution'].value[0] / \
                   page.tags['y_resolution'].value[1]
    assert x_resolution == y_resolution, \
        'x-resolution and y-resolution are not equal'
    size = page.tags['image_width'].value / x_resolution * 1e4
    date = datetime.datetime.strptime(
        page.tags['datetime'].value.decode(ENCODING),
        _DATETIME_FORMAT)

    # check version for backwards compatibility
    _convert_from_previous_metadata_versions(description)

    return {
        'run': description.get('mibi.run'),
        'version': description.get('mibi.version'),
        'coordinates': (
            _cm_to_micron(page.tags['x_position'].value),
            _cm_to_micron(page.tags['y_position'].value)),
        'date': date,
        'size': size,
        'slide': description.get('mibi.slide'),
        'fov_id': description.get('mibi.fov_id'),
        'fov_name': description.get('mibi.fov_name'),
        'folder': description.get('mibi.folder'),
        'dwell': description.get('mibi.dwell'),
        'scans': description.get('mibi.scans'),
        'aperture': description.get('mibi.aperture'),
        'instrument': description.get('mibi.instrument'),
        'tissue': description.get('mibi.tissue'),
        'panel': description.get('mibi.panel'),
        'mass_offset': description.get('mibi.mass_offset'),
        'mass_gain': description.get('mibi.mass_gain'),
        'time_resolution': description.get('mibi.time_resolution'),
        'miscalibrated': description.get('mibi.miscalibrated'),
        'check_reg': description.get('mibi.check_reg'),
        'filename': description.get('mibi.filename'),
        'description': description.get('mibi.description'),
        'optional_metadata': description.get('mibi.optional_metadata')
    }


def _convert_from_previous_metadata_versions(description):
    """Convert old metadata format to new one.

    This function ensures backwards compatibility for previous versions.
    """
    try:
        description['mibi.version']
    except KeyError:
        # if the key doesn't exist it means that the version was None and hence
        # not saved in the tiff file
        description['mibi.version'] = None

    if description['mibi.version'] != mi.MIBITIFF_VERSION:
        description['mibi.fov_name'] = description['mibi.description']
        description['mibi.fov_id'] = description['mibi.folder'].split('/')[0]
        description['mibi.description'] = None
        description['mibi.optional_metadata'] = {}
        description['mibi.version'] = mi.MIBITIFF_VERSION


def info(filename):
    """Gets the SIMS pages' metadata from a MibiTiff file.

    Args:
        filename: The path to the TIFF.

    Returns:
        A dictionary of metadata as could be supplied as kwargs to
        ``mibitof.mibi_image.MibiImage``, except with a ``channels`` key
        whose value is a list of (mass, target) tuples.
    """
    metadata = {}
    channels = []
    with TiffFile(filename) as tif:
        _check_software(tif)
        for page in tif.pages:
            description = _page_description(page)
            image_type = description['image.type'].lower()
            if image_type == 'sims':
                channels.append((description['channel.mass'],
                                 description['channel.target']))
                #  Get metadata on first SIMS page only
                if not metadata:
                    metadata.update(_page_metadata(page, description))
        metadata['conjugates'] = channels
        return metadata
