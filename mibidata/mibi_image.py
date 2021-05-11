"""Base module for working with MIBI images.

Copyright (C) 2021 Ionpath, Inc.  All rights reserved."""

import datetime
import os
import warnings

import numpy as np
from skimage import io as skio, transform

# The format of the run xml.
_DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S'
# The attributes to include in the metadata dictionary.
SPECIFIED_METADATA_ATTRIBUTES = ('date', 'run', 'coordinates', 'size', 'slide',
                                 'fov_id', 'fov_name', 'folder', 'dwell',
                                 'scans', 'aperture', 'instrument', 'tissue',
                                 'panel', 'mass_offset', 'mass_gain',
                                 'time_resolution', 'miscalibrated',
                                 'check_reg', 'filename', 'description',
                                 'version')



APERTURE_1MM = u'A'
APERTURE_300UM = u'B'
APERTURE_100UM = u'C'
APERTURE_30UM = u'D'
APERTURE_500UM = u'E'

APERTURE_MAP = {
    u'1 mm': APERTURE_1MM,
    u'300 \u03BCm': APERTURE_300UM,
    u'100 \u03BCm': APERTURE_100UM,
    u'30 \u03BCm': APERTURE_30UM,
    u'500 \u03BCm': APERTURE_500UM,
}

_IOX_APERTURE_MAP = {
    '1mm': APERTURE_1MM,
    '300um': APERTURE_300UM,
    '100um': APERTURE_100UM,
    '30um': APERTURE_30UM,
    '500um': APERTURE_500UM,
}

class MibiImage():
    """A multiplexed image with labeled channels and metadata.

    Args:
        data: An MxMxD numpy array of multiplexed image data, where D is
            the channel index and the frame size of the image is MxM.
        channels: A tuple of channel names of length D. The names may
            either be strings, or tuples of strings of the format (mass,
            target).
        kwargs: A mapping of arguments that used to define the image
            metadata. A list of required keys follows; however, the
            user can define other metadata key-value pairs that will be added
            as attributes to the class instance in use.

            * run: A string name of the run during which this image was
                acquired.
            * date: The run date. It can either be a datetime object,
                or a string. If a string, it will be parsed according to the
                ``datetime_format``.
            * coordinates: A tuple of (x, y) stage coordinates at which the
                image was acquired; stage coordinates should be in microns.
            * size: A float size of the image width/height in  :math:`\\mu m`.
            * slide: A string or integer slide ID.
            * fov_id: A string identifying the FOV within the run,
                i.e. 'FOV1' in MIBIcontrol or 'Point1' in earlier versions.
            * fov_name: A user-defined string name for the FOV as assigned
                before the run. In prior versions this was called 'point_name'.
            * folder: The folder name for this image as determined by the
                acquisition software. For data generated from MIBIcontrol
                software, this will the same as the fov_id.
            * dwell: A float pixel dwell time in :math:`ms`.
            * scans: A comma-separated list of image scan numbers.
            * aperture: Aperture code (e.g. 'A' or 'B') matching aperture width
                used during image acquisition.
            * instrument: A string identifier for the instrument used.
            * tissue: A string name of the tissue type.
            * panel: A string name of the panel used to stain the tissue.
            * version: A string identifier for the software version used.
            * datetime_format: The optional format of the date, if given as a
                string. Defaults to ``'%Y-%m-%dT%H:%M:%S'``.
            * mass_offset: Mass offset parameter used for mass calibration.
            * mass_gain: Mass gain used for mass calibration.
            * time_resolution: Parameter used for mass calibration.
            * miscalibrated: Whether or not there was significant difference
                between peak locations after mass recalibration.
            * check_reg: Whether or not the maximum shift between depths is
                higher than a threshold.
            * filename: The name of the instrument file containing the run
                metadata.
            * description: String describing any additional information about
                the image.

    Raises:
        ValueError: Raised if

            * the shape of data does not match length of channels.
            * the channel names are not unique.
            * the masses (if included in channel tuples) are not unique.
            * the targets (if included in channel tuples) are not unique.
            * the fov_id doesn't match the point in folder, unless the call
                is using the old point name format, in which case, only a
                warning is shown.

    Attributes:
        data: An MxMxD numpy array of multiplexed image data, where D is
            the channel index and the frame size of the image is MxM.
        channels: A tuple of channel names of length D. The names may
            either be strings, or tuples of strings of the format (mass,
            target).
        kwargs: A mapping of arguments that used to define the image
            metadata. A list of required keys follows; however, the
            user can define other metadata key-value pairs that will be added
            as attributes to the class instance in use.

            * run: A string name of the run during which this image was
                acquired.
            * date: The run date. It can either be a datetime object,
                or a string. If a string, it will be parsed according to the
                ``datetime_format``.
            * coordinates: A tuple of (x, y) stage coordinates at which the
                image was acquired; stage coordinates should be in microns.
            * size: A float size of the image width/height in  :math:`\\mu m`.
            * slide: A string or integer slide ID.
            * fov_id: A string identifying the FOV within the run,
                i.e. 'FOV1' in MIBIcontrol or 'Point1' in earlier versions.
            * fov_name: A user-defined string name for the FOV as assigned
                before the run. In prior versions this was called 'point_name'.
            * folder: The folder name for this image as determined by the
                acquisition software. For data generated from MIBIcontrol
                software, this will the same as the fov_id.
            * dwell: A float pixel dwell time in :math:`ms`.
            * scans: A comma-separated list of image scan numbers.
            * aperture: Aperture code (e.g. 'A' or 'B') matching aperture width
                used during image acquisition.
            * instrument: A string identifier for the instrument used.
            * tissue: A string name of the tissue type.
            * panel: A string name of the panel used to stain the tissue.
            * version: A string identifier for the software version used.
            * datetime_format: The optional format of the date, if given as a
                string. Defaults to ``'%Y-%m-%dT%H:%M:%S'``.
            * mass_offset: Mass offset parameter used for mass calibration.
            * mass_gain: Mass gain used for mass calibration.
            * time_resolution: Parameter used for mass calibration.
            * miscalibrated: Whether or not there was significant difference
                between peak locations after mass recalibration.
            * check_reg: Whether or not the maximum shift between depths is
                higher than a threshold.
            * filename: The name of the instrument file containing the run
                metadata.
            * description: String describing any additional information about
                the image.
    """

    def __init__(self, data, channels, **kwargs):

        # initialize non metadata attributes
        self._length = len(channels)
        if data.shape[2] != self._length:
            raise ValueError('Channels length does not match data dimensions.')
        self.data = data
        self._set_channels(channels, self._length)

        # initialize required metadata
        self._folder = None
        self._fov_id = None
        self._aperture = None
        date = kwargs.pop('date', None)
        datetime_format = kwargs.pop('datetime_format', _DATETIME_FORMAT)
        try:
            self.date = datetime.datetime.strptime(date, datetime_format)
        except TypeError:  # Given as datetime obj already, or None.
            self.date = date

        for attr in SPECIFIED_METADATA_ATTRIBUTES[1:]:
            setattr(self, attr, kwargs.pop(attr, None))

        # empty list for storing user-defined attribute names
        self._user_defined_attributes = []

        # whatever remains (if anything) is user-defined metadata
        for k, v in kwargs.items():
            setattr(self, k, v)
            self._user_defined_attributes.append(k)

    def add_attr(self, **kwargs):
        """Adds user-defined metadata key-value pairs as attributes to
           the class instance in use. If attribute already exists
           for the current instance, raises an error.

        Args:
            kwargs: A mapping of arguments for a user to add multiple
                    attributes with their respecitve
                    values.
        Raises:
            ValueError: Raised if attempts to set an attribute that is already
            defined for this instance.

        """
        already_defined = [attr for attr in kwargs if hasattr(self, attr)]
        if already_defined:
            if len(already_defined) == 1:
                already_def_error = (f'{already_defined[0]} is already '
                                     f'an attribute of this instance.')
            else:
                already_def_error = (f'{", ".join(already_defined)} are '
                                     f'already attributes for this instance.')
            raise ValueError(already_def_error)
        for key, value in kwargs.items():
            self._user_defined_attributes.append(key)
            setattr(self, key, value)


    def remove_attr(self, attributes):
        """Removes user-defined attributes from the class instance in use.

        Args:
            attributes: A single string or a list of user-defined attributes
                        for deletion.

        Raises:
            ValueError: Raised if

                * attempts to remove a required attribute.
                * an attribute is not defined for this instance.
        """
        if isinstance(attributes, str):
            attributes = [attributes]
        required_rem = [attr for attr in attributes if attr
                        in SPECIFIED_METADATA_ATTRIBUTES]
        no_attr = [attr for attr in attributes if not hasattr(self, attr)]
        if required_rem:
            if len(required_rem) == 1:
                required_error = (f'{required_rem[0]} is a required '
                                  f'attribute.')
            else:
                required_error = (f'{", ".join(required_rem)} are required '
                                  f'attributes.')
            raise ValueError(required_error)
        if no_attr:
            if len(no_attr) == 1:
                required_error = (f'{no_attr[0]} is not an attribute '
                                  f'of this instance.')
            else:
                required_error = (f'{", ".join(no_attr)} are not attributes '
                                  f'of this instance.')
            raise ValueError(required_error)
        for attr in attributes:
            delattr(self, attr)
            self._user_defined_attributes.remove(attr)

    @property
    def pixel_size(self):
        """Returns the diameter of a pixel in microns."""
        # pylint: disable=no-member
        if not self.size:
            raise ValueError('Pixel size not available if FOV size is not set.')
        return self.size / self.data.shape[0]

    @property
    def point_name(self):
        """Returns fov_name instead of deprecated point_name."""
        return self.fov_name

    @point_name.setter
    def point_name(self, value):
        """Convert deprecated point_name to fov_name."""
        warnings.warn('The "point_name" attribute is deprecated. '
                      'Setting "fov_name" to "{}".'.format(value))
        self.fov_name = value  # pylint: disable=attribute-defined-outside-init

    @property
    def folder(self):
        return self._folder

    @folder.setter
    def folder(self, value):
        """Enforce consistency with fov_id."""
        if value:
            fov = value.split('/')[0]
            if not self.fov_id:
                self._fov_id = fov
            elif self.fov_id != fov:
                raise ValueError('fov_id must match folder, but here '
                                 f'fov_id={self.fov_id} and you are trying to '
                                 f'set folder to {value}. Use the `set_fov_id` '
                                 'method instead.')
            self._folder = value

    @property
    def fov_id(self):
        return self._fov_id

    @fov_id.setter
    def fov_id(self, value):
        """Enforce consistency with folder."""
        if not self.folder:
            self._folder = value
        elif value != self.folder.split('/')[0]:
            raise ValueError('fov_id must match folder, but here '
                             f'folder={self.folder} and you are trying to set '
                             f'fov_id to {value}. Use the `set_fov_id` '
                             'method instead.')
        self._fov_id = value

    def set_fov_id(self, fov_id, folder=None):
        """Sets the fov_id and optionally updates the folder to match.

        Args:
            fov_id: The fov id within the run such as FOV1, or if from a beta
                system Point1.
            folder: For compatibility with beta systems, the folder containing
                the fov data, such as Point1/RowNumber0/Depth_Profile0. If
                omitted, this will default to match the fov id.
        """
        if folder:
            if folder.split('/')[0] != fov_id:
                raise ValueError('fov_id must match the top level folder.')
            self._folder = folder
        if folder is None and self.folder.split('/')[0] != fov_id:
            self._folder = fov_id
        self._fov_id = fov_id

    @property
    def aperture(self):
        return self._aperture

    @aperture.setter
    def aperture(self, value):
        self._aperture = self.parse_aperture(value)

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

    def _set_channels(self, channels, length):
        if len(set(channels)) != length:
            raise ValueError('Channels are not all unique.')
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
        self._channels = tuple(channels)

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

    def __repr__(self):
        s = f'{type(self)}\n'
        s += '\n'.join(f'{key}: {val}' for key, val in self.metadata().items())
        return s

    def __str__(self):
        s = f'{type(self)} ' + '{'
        s += ', '.join(f'{key}: {val}' for key, val in self.metadata().items())
        s += '}'
        return s

    @staticmethod
    def parse_aperture(value):
        """
        Args:
            value: A string representing an aperture code.
        Returns:
            An aperture code (e.g. 'A' or 'B') matching aperture width
            used during image acquisition.
        Raises:
            ValueError: Raised if the value parameter cannot be mapped to an
            aperture code.
        """
        if value in APERTURE_MAP.values() or value is None:
            # Allow valid aperture codes or None
            aperture = value
        else:
            # Convert known string aperture parameters, if possible
            try:
                unified_map = {
                    **_IOX_APERTURE_MAP,
                    **APERTURE_MAP
                }
                aperture = unified_map[value]
                warnings.warn(
                    'Deprecated aperture code \'{}\', converting to \'{}\'. In '
                    'a future version, values from the following map will be '
                    'required: {}'.format(value,
                                          unified_map[value],
                                          APERTURE_MAP))
            except KeyError:
                raise ValueError(
                    'Invalid aperture code \'{}\', must use values'
                    'from the following map: {}'.format(value, APERTURE_MAP)
                )
        return aperture

    def metadata(self):
        """Returns a dictionary of the image's metadata."""
        metadata_keys = list(SPECIFIED_METADATA_ATTRIBUTES)
        # find user-defined metadata
        metadata_keys.extend(self._user_defined_attributes)
        return {key: getattr(self, key) for key in metadata_keys}

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
                error_msg = f'Cannot match {channels}. Channels were indexed ' \
                    f'with targets only (no masses were given), available ' \
                    f'targets are {self._channels}'
            else:
                missing_channels = []
                matches = []
                keys = [channel[1] for channel in self._channels]

                # check for missing channels
                # match on case-insensitive substring
                for channel in channels:
                    if channel in keys:
                        continue
                    missing_channels.append(channel)
                    if len(channel) < 3:
                        continue
                    matches += [match for match in keys if channel.lower() in \
                        match.lower()]

                error_msg = f'Channels, targets or masses not found ' \
                    f'matching {missing_channels}. '

                if matches:
                    error_msg += f'Did you mean {matches}? '

                error_msg += f'Available targets are {keys}.'
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
            ValueError: Raised if

                * The image has any channels already present on
                  instance to which it is being appended.
                * The channels to be appended do not match the form of the
                  channels of the original image.
        """
        if set(self.channels).intersection(set(image.channels)):
            raise ValueError('Images contain overlapping channels.')
        if all((isinstance(c, tuple) and len(c) == 2 for c in self.channels)):
            if not all((isinstance(c, tuple) and len(c) == 2
                        for c in image.channels)):
                raise ValueError('Channels to be appended must match form of '
                                 'original image, which is a list of tuples in '
                                 'format (mass, target).')
        if all(isinstance(c, str) for c in self.channels):
            if not all(isinstance(c, str) for c in image.channels):
                raise ValueError('Channels to be appended must match form of '
                                 'original image, which is a list of str.')
        self._set_channels(
            [c for c in self.channels] + [c for c in image.channels],
            len(self.channels) + len(image.channels))
        self.data = np.concatenate((self.data, image.data), axis=2)

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
            ratio = float(size[1]) / size[0]
        except TypeError:
            ratio = 1
            size = (size, size)
        if ratio != float(shape[1]) / shape[0]:
            raise ValueError(
                'The input image layers have shape %s and cannot be resized '
                'to %s without changing the aspect ratio.' % (shape, size))
        if preserve_type:
            dtype = self.data.dtype
        else:
            dtype = float

        def _resize():
            return transform.resize(
                self.data, (size[0], size[1], shape[2]), order=3,
                mode='edge', preserve_range=True,
                anti_aliasing=False).astype(dtype)

        if copy:
            return MibiImage(_resize(), self.channels, **self.metadata())
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
        if (data.dtype in (np.uint8, np.uint16, bool) or
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

    def rename_targets(self, channel_map):
        """Modifies target names according to the specified map

        Args:
            channel_map: A dict where each key is an existing target name
                that is to be changed, and the value is the desired new
                target name.
        """
        existing = list(self.channels)
        for key in channel_map:
            index = self.channel_inds(key)
            if isinstance(existing[index], tuple):
                existing[index] = existing[index][0], channel_map[key]
            else:
                existing[index] = channel_map[key]
        self.channels = existing
