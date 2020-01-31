"""Read and write to and from IONpath MIBItiff files.

Copyright (C) 2019 Ionpath, Inc.  All rights reserved."""

import collections
from fractions import Fraction
import datetime
import json
import os
import warnings

import numpy as np
from skimage.external.tifffile import TiffFile, TiffWriter

from mibidata import mibi_image as mi, util

# Increment this when making functional changes.
SOFTWARE_VERSION = 'IonpathMIBIv1.0'
# These are reserved by the tiff writer and cannot be specified by the user.
RESERVED_MIBITIFF_ATTRIBUTES = ('image.type', 'SIMS', 'channel.mass',
                                'channel.target', 'shape')
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

REQUIRED_METADATA_ATTRIBUTES = ('fov_id', 'fov_name', 'run', 'folder',
                                'dwell', 'scans', 'mass_gain', 'mass_offset',
                                'time_resolution', 'coordinates', 'size',
                                'masses', 'targets')

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
          multichannel=True, dtype=None, write_float=None):
    """Writes MIBI data to a multipage TIFF.

    Args:
        filename: The path to the target file if multi-channel, or the path to
            a folder if single-channel.
        image: A :class:`mibidata.mibi_image.MibiImage` instance.
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
        dtype: dtype: One of (``np.float32``, ``np.uint16``) to force the dtype
            of the saved image data. Defaults to ``None``, which chooses the
            format based on the data's input type, and will convert to
            ``np.float32`` or ``np.uint16`` from other float or int types,
            respectively, if it can do so without a loss of data.
        write_float: Deprecated, will raise ValueError if specified. To
            specify the dtype of the saved image, please use the `dtype`
            argument instead.

    Raises:
        ValueError: Raised if

            * The image is not a :class:`mibidata.mibi_image.MibiImage`
              instance.
            * The :class:`mibidata.mibi_image.MibiImage` coordinates, size,
              fov_id, fov_name, run, folder, dwell, scans, mass_gain,
              mass_offset, time_resolution, masses or targets are None.
            * `dtype` is not one of ``np.float32`` or ``np.uint16``.
            * `write_float` has been specified.
            * Converting the native :class:`mibidata.mibi_image.MibiImage` dtype
              to the specified or inferred ``dtype`` results in a loss of data.
    """
    if not isinstance(image, mi.MibiImage):
        raise ValueError('image must be a mibidata.mibi_image.MibiImage '
                         'instance.')
    missing_required_metadata = [m for m in REQUIRED_METADATA_ATTRIBUTES
                                 if not getattr(image, m)]
    if missing_required_metadata:
        if len(missing_required_metadata) == 1:
            missing_metadata_error = (f'{missing_required_metadata[0]} is '
                                      f'required and may not be None.')
        else:
            missing_metadata_error = (f'{", ".join(missing_required_metadata)}'
                                      f' are required and may not be None.')
        raise ValueError(missing_metadata_error)

    if write_float is not None:
        raise ValueError('`write_float` has been deprecated. Please use the '
                         '`dtype` argument instead.')
    if dtype and not dtype in [np.float32, np.uint16]:
        raise ValueError('Invalid dtype specification.')

    if dtype == np.float32:
        save_dtype = np.float32
        range_dtype = 'd'
    elif dtype == np.uint16:
        save_dtype = np.uint16
        range_dtype = 'I'
    elif np.issubdtype(image.data.dtype, np.floating):
        save_dtype = np.float32
        range_dtype = 'd'
    else:
        save_dtype = np.uint16
        range_dtype = 'I'

    to_save = image.data.astype(save_dtype)
    if not np.all(np.equal(to_save, image.data)):
        raise ValueError('Cannot convert data from '
                         f'{image.data.dtype} to {save_dtype}')

    if ranges is None:
        ranges = [(0, m) for m in to_save.max(axis=(0, 1))]

    coordinates = [
        (286, '2i', 1, _micron_to_cm(image.coordinates[0])),  # x-position
        (287, '2i', 1, _micron_to_cm(image.coordinates[1])),  # y-position
    ]
    resolution = (image.data.shape[0] * 1e4 / float(image.size),
                  image.data.shape[1] * 1e4 / float(image.size),
                  'cm')

    # The mibi. prefix is added to attributes defined in the spec.
    # Other user-defined attributes are included too but without the prefix.
    prefixed_attributes = mi.SPECIFIED_METADATA_ATTRIBUTES[1:]
    description = {}
    for key, value in image.metadata().items():
        if key in prefixed_attributes:
            description[f'mibi.{key}'] = value
        elif key in RESERVED_MIBITIFF_ATTRIBUTES:
            warnings.warn(f'Skipping writing user-defined {key} to the '
                          f'metadata as it is a reserved attribute.')
        elif key != 'date':
            description[key] = value
    # TODO: Decide if should filter out those that are None or convert to empty
    # string so that don't get saved as 'None'

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

                infile.save(
                    to_save[:, :, i], compress=6, resolution=resolution,
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

            target_filename = os.path.join(
                filename, '{}.tiff'.format(
                    util.format_for_filename(image.targets[i])))

            with TiffWriter(target_filename,
                            software=SOFTWARE_VERSION) as infile:

                infile.save(
                    to_save[:, :, i], compress=6, resolution=resolution,
                    metadata=metadata, datetime=image.date,
                    extratags=page_tags)


def read(file, sims=True, sed=False, optical=False, label=False,
         inc_channels=None):
    """Reads MIBI data from an IonpathMIBI TIFF file.

    Args:
        file: The string path or an open file object to a MIBItiff file.
        sims: Boolean for whether to return the SIMS (MIBI) data. Defaults to
            True.
        sed: Boolean for whether to return the SED data. Defaults to False.
        optical: Boolean for whether to return the optical image. Defaults to
            False.
        label: Boolean for whether to return the slide label image. Defaults to
            False.
        inc_channels: List or tuple of channel names to include in MibiImage.
                      Names should be string tuples of format (mass, target).

    Returns: A tuple of the image types set to True in the parameters, in the
        order SIMS, SED, Optical, Label (but including only those types
        specified). The SIMS data will be returned as a
        :class:`mibidata.mibi_image.MibiImage` instance; the other image
        types will be returned as numpy arrays. If an image type is selected to
        be returned  but is not present in the image, it will be returned as
        None. If returning SIMS data and the inc_channels parameter is set, only
        those channels will be included in the MibiImage instance.

    Raises:
        ValueError: Raised if the input file is not of the IonpathMIBI
            format, or if no image type selected to be returned.
    """
    return_types = collections.OrderedDict([
        ('sims', sims), ('sed', sed), ('optical', optical), ('label', label)
    ])
    if not any((val for val in return_types.values())):
        raise ValueError('At least one image type must be specified to return.')
    if (inc_channels and not isinstance(inc_channels, (list, tuple)) and not
            isinstance(inc_channels[0], tuple)):
        raise ValueError('The parameter inc_channels must be a tuple or list '
                         'that contains string tuples in the format '
                         '(mass, target).')
    to_return = {}
    metadata = {}
    sims_data = []
    channels = []
    with TiffFile(file) as tif:
        _check_software(tif)
        for page in tif.pages:
            description, image_type = _page_description(page)
            if sims and image_type == 'sims':
                if _get_page_data(page, description, metadata, channels,
                                  inc_channels):
                    sims_data.append(page.asarray())
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
    """Loads and decodes the JSON description and image type in a
       TIFF page.
    """
    description = json.loads(
        page.tags['image_description'].value.decode(ENCODING))
    image_type = description['image.type'].lower()
    return description, image_type

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
    _convert_from_previous(description)

    metadata = {}
    for key, val in description.items():
        if key.startswith('mibi.'):
            metadata[key[5:]] = val
        elif key not in RESERVED_MIBITIFF_ATTRIBUTES:
            metadata[key] = val

    metadata.update({
        'coordinates': (
            _cm_to_micron(page.tags['x_position'].value),
            _cm_to_micron(page.tags['y_position'].value)),
        'date': date,
        'size': size})

    return metadata


def _convert_from_previous(description):
    """Convert old metadata format for backwards compatibility.

    Most of these conversions would happen during MibiImage construction,
    but we do them here in case reading the info only.
    """
    match_needed = False
    if not description.get('mibi.fov_name') and description.get(
            'mibi.description'):
        description['mibi.fov_name'] = description.pop('mibi.description')
    if description.get('mibi.folder'):
        description['mibi.fov_id'] = ''
        value = 'mibi.folder'
        field = 'mibi.fov_id'
        match_needed = True
    if description.get('mibi.fov_id'):
        description['mibi.folder'] = ''
        value = 'mibi.fov_id'
        field = 'mibi.folder'
        match_needed = True
    if match_needed:
        description[field] = mi.MibiImage.match_fov_folder(
            description[value], description[field], value.split('.')[1],
            field.split('.')[1])
    if description.get('mibi.aperture'):
        description['mibi.aperture'] = mi.MibiImage.parse_aperture(
            description['mibi.aperture'])

def _get_page_data(page, description, metadata, channels, inc_channels=None):
    """Adds to metadata and channel info for single TIFF page.

    Args:
        page: Single page in TIFF file.
        description: Decoded JSON description.
        metadata: Dictionary of metadata for entire TIFF file to add to.
        channels: List of channels for entire TIFF file to add to.
        inc_channels: If set, only these channels will be added to channel
                      parameter.

    Returns:
        include: Boolean representing whether channel should be included or not.
    """
    # Get metadata on first SIMS page only
    if not metadata:
        metadata.update(_page_metadata(page, description))
    if inc_channels:
        if (description['channel.mass'],
                description['channel.target']) not in inc_channels:
            return False
    channels.append((description['channel.mass'],
                     description['channel.target']))
    return True

def info(filename, inc_channels=None):
    """Gets the metadata from a MibiTiff file.

    Args:
        filename: The path to the TIFF.
        inc_channels: List or tuple of channel names to include in MibiImage.
                      Names should be string tuples of format (mass, target).

    Returns:
        A dictionary of metadata as could be supplied as kwargs to
        :class:`mibidata.mibi_image.MibiImage`, except with a ``conjugates`` key
        whose value is a list of (mass, target) tuples. If inc_channels is set,
        then the metadata ``conjugates`` key only contains information for those
        channels.
    """
    if (inc_channels and not isinstance(inc_channels, (list, tuple)) and not
            isinstance(inc_channels[0], tuple)):
        raise ValueError('The parameter inc_channels must be a tuple or list '
                         'that contains string tuples in the format '
                         '(mass, target).')
    metadata = {}
    channels = []
    with TiffFile(filename) as tif:
        _check_software(tif)
        for page in tif.pages:
            description, image_type = _page_description(page)
            if image_type == 'sims':
                _get_page_data(page, description, metadata, channels,
                               inc_channels)
        metadata['conjugates'] = channels
        return metadata
