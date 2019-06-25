"""Base module for working with MIBI images.

Copyright (C) 2019 Ionpath, Inc.  All rights reserved."""

import datetime
import os
import warnings

import numpy as np
from skimage import io as skio, transform

# THe format of the run xml.
_DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S'
# The attributes to include in the metadata dictionary.
_ATTRIBUTES = ('run', 'date', 'coordinates', 'size', 'slide', 'point_name',
               'folder', 'dwell', 'scans', 'aperture',
               'instrument', 'tissue', 'panel', 'version', 'mass_offset',
               'mass_gain', 'time_resolution', 'miscalibrated', 'check_reg',
               'filename')


class MibiImage():
    """A multiplexed image with labeled channels and metadata.

    Args:
        data: An MxMxD numpy array of multiplexed image data, where D is
            the channel index and the frame size of the image is MxM.
        channels: A tuple of channel names of length D. The names may
            either be strings, or tuples of strings of the format (mass,
            target).
        run: A string name of the run during which this image was acquired.
        date: The run date. It can either be a datetime object, or a string.
            If a string, it will be parsed according to the
            `datetime_format``.
        coordinates: A tuple of (x, y) stage coordinates at which the image
            was acquired.
        size: A float size of the image width/height in  :math:`\\mu m`.
        slide: A string or integer slide ID.
        point_name: A string name for the point as assigned during the run.
        folder: The folder name for this image as determined by the
            acquisition software.
        dwell: A float pixel dwell time in :math:`ms`.
        scans: A comma-separated list of image scan numbers.
        aperture: A string name of the aperture used during image
            acquisition.
        instrument: A string identifier for the instrument used.
        tissue: A string name of the tissue type.
        panel: A string name of the panel used to stain the tissue.
        version: A string identifier for the software version used.
        datetime_format: The optional format of the date, if given as a
            string. Defaults to ``'%Y-%m-%dT%H:%M:%S'``.
        mass_offset: Mass offset parameter used for mass calibration.
        mass_gain: Mass gain used for mass calibration.
        time_resolution: Parameter used for mass calibration.
        miscalibrated: Whether or not there was significant difference between
            peak locations after mass recalibration.
        check_reg: Whether or not the maximum shift between depths is higher
            than a threshold.

    Raises:
        ValueError: Raised if

            - the shape of data does not match length of channels.
            - the channel names are not unique.
            - the masses (if included in channel tuples) are not unique.
            - the targets (if included in channel tuples) are not unique.

    Attributes:
        data: An MxMxD numpy array of multiplexed image data, where D is
            the channel index and the frame size of the image is MxM.
        channels: A tuple of channel names of length D. The names may
            either be strings, or tuples of strings of the format (mass,
            target).
        masses: A tuple of the masses of the channels, if the channels were
            given as (mass, target) tuples; otherwise None.
        targets: A tuple of the targets of the channels, if the channels were
            given as (mass, target) tuples; otherwise None.
        run: A string name of the run during which this image was acquired.
        date: A datetime object of the run date.
        coordinates: A tuple of (x, y) stage coordinates at which the image
            was acquired.
        size: A float size of the image width/height in :math:`\\mu m`.
        slide: A string or integer slide ID.
        point_name: A string name for the point as assigned during the run.
        folder: The folder name for this image as determined by the
            acquisition software.
        dwell: A float pixel dwell time in :math:`ms`.
        scans: A comma-separated list of image scan numbers.
        aperture: A string name of the aperture used during image
            acquisition.
        instrument: A string identifier for the instrument used.
        tissue: A string name of the tissue type.
        panel: A string name of the panel used to stain the tissue.
        version: A string identifier for the software version used.
        mass_offset: Mass offset parameter used for mass calibration.
        mass_gain: Mass gain used for mass calibration.
        time_resolution: Parameter used for mass calibration.
        miscalibrated: Whether or not there was significant difference between
            peak locations after mass recalibration.
        check_reg: Whether or not the maximum shift between depths is higher
            than a threshold.
        filename: The name of the Run XML file which corresponds to the run
            name.
    """

    # pylint: disable=too-many-arguments
    def __init__(self, data, channels, run=None, date=None,
                 coordinates=None, size=None, slide=None, point_name=None,
                 folder=None, dwell=None, scans=None, aperture=None,
                 instrument=None, tissue=None, panel=None, version=None,
                 mass_offset=None, mass_gain=None, time_resolution=None,
                 miscalibrated=None, check_reg=None,
                 datetime_format=_DATETIME_FORMAT, filename=None):

        self._length = len(channels)
        if data.shape[2] != self._length:
            raise ValueError('Channels length does not match data dimensions.')
        self.data = data
        self._set_channels(channels, self._length)

        try:
            self.date = datetime.datetime.strptime(date, datetime_format)
        except TypeError:  # Given as datetime obj already, or None.
            self.date = date

        self.run = run
        self.coordinates = coordinates
        self.size = size
        self.slide = slide
        self.point_name = point_name
        self.folder = folder
        self.dwell = dwell
        self.scans = scans
        self.aperture = aperture
        self.instrument = instrument
        self.tissue = tissue
        self.panel = panel
        self.version = version
        self.mass_offset = mass_offset
        self.mass_gain = mass_gain
        self.time_resolution = time_resolution
        self.miscalibrated = miscalibrated
        self.check_reg = check_reg
        self.filename = filename

    @property
    def channels(self):
        """A tuple of channel names.

        The names may either be strings, or tuples of strings of the format
        (mass, target).
        """
        return self._channels

    @channels.setter
    def channels(self, values):
        """A tuple of channel names.

        The names may either be strings, or tuples of strings of the format
        (mass, target).
        """
        self._set_channels(values, self._length)

    @property
    def labels(self):
        """For backwards compatibility.

        This may be removed in a future version. Use the :attr:`~channels`
        property instead.
        """
        return self.channels

    @labels.setter
    def labels(self, values):
        """This property is for backwards compatibility only.

        This may be removed in a future version. Use the :attr:`~channels`
        property instead.
        """
        self._set_channels(values, self._length)

    def _set_channels(self, channels, length):
        if len(set(channels)) != length:
            raise ValueError('Channels are not all unique.')
        self._channels = tuple(channels)
        if all((isinstance(c, tuple) and len(c) == 2 for c in channels)):
            # Tuples of masses and targets.
            masses, targets = zip(*channels)
            if len(set(masses)) != length:
                raise ValueError('Masses are not all unique.')
            if len(set(targets)) != length:
                raise ValueError('Targets are not all unique.')
            self.masses = masses
            self.targets = targets
        elif all(isinstance(c, str) for c in channels):
            self.masses = self.targets = None
        else:
            raise ValueError(
                'Channels must be a list of tuples of (int, str) or a '
                'list of str')

    def __eq__(self, other):
        """Checks for equality between MibiImage instances.

        Args:
            other: A MibiImage.

        Returns: True if both the values of the data array and the metadata of
            the other MibiImage are equal to this instance's; otherwise False.
        """
        if isinstance(other, self.__class__):
            return (self.metadata() == other.metadata() and
                    self.channels == other.channels and
                    self.data.dtype == other.data.dtype and
                    np.all(self.data == other.data))
        return False

    def __getitem__(self, channels):
        """Equivalent to :meth:`~slice_data`."""
        return self.slice_data(channels)

    def metadata(self):
        """Returns a dictionary of the image's metadata."""
        return {key: getattr(self, key) for key in _ATTRIBUTES}

    def channel_inds(self, channels):
        """Returns the indices of the specified channels on the data's 2nd axis.

        Args:
            channels: A single channel, mass or target label; or, a sequence of
                channels, masses, or targets.

        Returns:
            A scalar or numpy array of the indices of the specified channels.

        Raises:
            KeyError: Raised if channels are not all found in image.
        """
        try:
            return self._channels.index(channels)
        except ValueError:
            pass
        try:
            return self.targets.index(channels)
        except (ValueError, AttributeError):
            pass
        try:
            return self.masses.index(channels)
        except (ValueError, AttributeError):
            pass
        try:
            return [self._channels.index(i) for i in channels]
        except ValueError:
            pass
        try:
            return [self.masses.index(i) for i in channels]
        except (ValueError, AttributeError):
            pass
        try:
            return [self.targets.index(i) for i in channels]
        except (ValueError, AttributeError):
            if self.targets is None:
                error_msg = f'Channels were indexed with targets only (no ' \
                    f'masses were given), available targets are ' \
                    f'{self._channels}'
            else:
                error_msg = f'Subset of channels, targets or massses not ' \
                    f'found matching {self._channels}'

            raise KeyError(error_msg)

    def slice_data(self, channels):
        """Selects a subset of data from the MibiImage given selected channels.

        If a single channel is given, the third dimension will be
        stripped and an actual slice of the array will be returned, not a copy.

        If a sequence of channels is given, even if it is a sequence of
        length 1, a copy will be returned.

        This method can also be called by indexing with ``[]`` (i.e.
        :meth:`~__getitem__`.  See also :meth:`~slice_image`.

        Args:
            channels: A single channel, mass or target label; or, a sequence of
                channels, masses, or targets.

        Returns:
            A numpy array containing the data sliced from the image.
        """
        return self.data[:, :, self.channel_inds(channels)]

    def slice_image(self, channels):
        """Returns a MibiImage from slicing channels of another MibiImage.

        See also: :meth:`~slice_data`.

        Args:
            channels: A single channel, mass or target label; or, a sequence of
                channels, masses, or targets.

        Returns:
            A new MibiImage instance containing a copy of the data and
            metadata of the selected channels.
        """
        data = self.slice_data(channels)
        inds = self.channel_inds(channels)
        if data.ndim == 2:
            data = data.copy()[:, :, np.newaxis]
            new_channels = [self.channels[inds]]
        else:
            new_channels = [self.channels[i] for i in inds]
        return MibiImage(data, new_channels, **self.metadata())

    def copy(self):
        """Creates a new MibiImage instance with a copy of the data.

        Returns:
            A MibiImage instance with a copy of the data and channels.
        """
        return MibiImage(self.data.copy(), self.channels[:], **self.metadata())

    def append(self, image):
        """Appends another MibiImage's data and channels.

        Note that only the channels and data will be affected; the initial
        metadata will be preserved.

        Args:
            image: A MibiImage.

        Raises:
            ValueError: Raised if the image has any channels already present on
                instance to which it is being appended.
        """
        if set(self.channels).intersection(set(image.channels)):
            raise ValueError('Images contain overlapping channels.')
        self.data = np.concatenate((self.data, image.data), axis=2)
        self._set_channels(
            [c for c in self.channels] + [c for c in image.channels],
            len(self.channels) + len(image.channels))

    def remove_channels(self, channels, copy=False):
        """Removes specified channels from a MibiImage.

        Args:
            channels: A list or tuple of labels of channels to remove.
            copy: Boolean defaulting to `False` for whether to return a new
                MibiImage with the channels' data removed. If `False`,
                the data, channels, masses and targets attributes of the input
                image are directly altered.

        Returns:
            If `copy=True`, returns a MibiImage with copies of all
            channels except those specified to be removed from the initial
            image.
        """
        # np.delete does not alter the input array
        new_data = np.delete(self.data, self.channel_inds(channels), 2)
        delete_inds = self.channel_inds(channels)
        new_channels = [
            c for c in self.channels if self.channel_inds(c) not in delete_inds]
        if copy:
            return MibiImage(new_data, new_channels, **self.metadata())
        self.__init__(new_data, new_channels, **self.metadata())
        return None

    def resize(self, size, copy=False, preserve_type=False):
        """Resizes the image.

        This uses a bicubic transformation on each channel, and converts the
        image data to floats in the unit interval according to
        skimage.img_as_float. That means that uint data is scaled out of the
        max of its type, i.e. 255 or 65535. If alternate scaling is desired,
        it should be performed prior to resizing.

        Args:
            size: An integer or tuple that determines the size of the first
                two dimensions of the returned image. If an integer,
                it is expanded to the tuple (size, size).
            copy: Boolean defaulting to `True` for whether to alter the data
                directly.
            preserve_type: Boolean defaulting to `False` for whether the
                returned data is of the same dtype. If `False`, the data is
                converted to floats in the unit interval according to
                skimage.img_as_float. That means that uint data is scaled out
                of the max of its type, i.e. 255 or 65535. If `True`, the data
                makes a round trip through floats and thus may lose precision
                when it is converted back to its original dtype.

        Returns:
            If `copy=False`, returns a MibiImage of the resized data. The
            dtype is determined by `preserve_type`.

        Raises:
            ValueError: Raised if the input size would change the aspect ratio
                of the image.
        """
        shape = self.data.shape
        try:
            ratio = np.float(size[1]) / size[0]
        except TypeError:
            ratio = 1
            size = (size, size)
        if ratio != np.float(shape[1]) / shape[0]:
            raise ValueError(
                'The input image layers have shape %s and cannot be resized '
                'to %s without changing the aspect ratio.' % (shape, size))
        if preserve_type:
            dtype = self.data.dtype
        else:
            dtype = np.float

        def _resize():
            with warnings.catch_warnings():
                warnings.filterwarnings(
                    'ignore',
                    message='Anti-aliasing will be enabled by default.*')
                return transform.resize(
                    self.data, (size[0], size[1], shape[2]), order=3,
                    mode='edge', preserve_range=True,
                    anti_aliasing=False).astype(dtype)

        if copy:
            return MibiImage(_resize(), self.labels, **self.metadata())
        self.data = _resize()

    def export_pngs(self, path, size=None):
        """Saves each channel of a MibiImage as a grayscale png.

        If the image data are boolean or integers of any type and are within
        the range of uint8, the values are converted to uint8 before saving.

        If the image data are integers of any type and not within the range of
        uint8 but are within the range of uint16, they are converted to uint16
        before saving.

        Otherwise a TypeError is raised.

        For image data that is float, use `mibitof.tiff.write()` for writing
        as TIFFs, since PNGs do not support float type.

        Args:
            path: The path to the folder in which to save the images. This
                folder must already exist.
            size: If None, the images are saved at full resolution. If an
                integer or tuple, the images are resized by passing this
                parameter to :meth:`resize`.

        Raises:
            TypeError: Raised if the data type and/or range is unsupported.
        """
        if size is not None:
            data = self.resize(size, copy=True, preserve_type=True).data
        else:
            data = self.data

        # Checking min and max for the entire image stack, not each layer,
        # so that the dtype for saved images is consistent.
        dmin = data.min()
        dmax = data.max()
        if (data.dtype in (np.uint8, np.uint16, np.bool) or
                np.issubdtype(data.dtype, np.integer)):
            # save as uint8 or uint 16 if already in those ranges
            if dmin >= 0 and dmax < 2 ** 8:
                converter = lambda array: array.astype(np.uint8)
            elif dmin >= 0 and dmax < 2 ** 16:
                converter = lambda array: array.astype(np.uint16)
            else:
                raise TypeError(
                    'Data are integers outside of uint16 range. You must '
                    'rescale before exporting.')
        else:
            raise TypeError('Unsupported dtype: %s' % data.dtype.type)

        for i, label in enumerate(self.channels):
            im = converter(data[:, :, i])
            png_name = (label[1] if isinstance(label, tuple) else label
                       ).replace('/', '-')  # / isn't safe for filenames
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore',
                                        message='.*low contrast image.*')
                skio.imsave(f'{os.path.join(path, png_name)}.png', im)
