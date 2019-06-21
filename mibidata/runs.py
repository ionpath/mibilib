"""Utilities for working with MIBI run metadata.

Copyright (C) 2019 Ionpath, Inc.  All rights reserved."""

import os
import re
import xml.etree.ElementTree as ElementTree

import numpy as np

MASS_CALIBRATION_PARAMETERS = ('TimeResolution', 'MassGain', 'MassOffset',
                               'XSize', 'YSize')
FOV_PATTERN = re.compile('^(Depth_Profile|Chemical_Image)$')
_MICRONS_PER_MOTOR_STEP = 0.1  # motor step in microns

def parse_xml(path):
    """Read a run XML and return a list of image metadata dicts, plus a
    dict of the mass calibration and other msdf metadata.

    Args:
        path: A path to a run XML file.

    Returns:
        fovs: A list of image metadata dicts for each FOV.
        calibration: A dict containing mass calibration parameters.
    """
    run = os.path.splitext(os.path.split(path)[1])[0]
    fovs = []
    calibration = {}
    tree = ElementTree.parse(path)
    calibration['RasterStyle'] = tree.getroot().attrib.get('RasterStyle')
    runtime = tree.find('./Root').attrib.get('RunTime')
    # Hack for when run has crashed midway through and datetime is unavailable.
    if runtime == '0001-01-01T00:00:00':
        runtime = None
    for j, point in enumerate(tree.findall('./Root/Point'), 1):
        number = 'Point{}'.format(j)
        counter = {'Depth_Profile': 0, 'Chemical_Image': 0}
        name = point.attrib.get('PointName')
        for item in point:
            match = re.match(FOV_PATTERN, item.tag)
            if item.tag.startswith('RowNumber'):
                row_num = item.tag
                coordinates = (
                    float(item.attrib.get('XAttrib')) * _MICRONS_PER_MOTOR_STEP,
                    float(item.attrib.get('YAttrib')) * _MICRONS_PER_MOTOR_STEP)
                continue
            elif match:
                parent = '{}{}'.format(match.group(1), counter[match.group(1)])
                counter[match.group(1)] += 1
                folder = os.path.join(number, row_num, parent)
                for param in MASS_CALIBRATION_PARAMETERS:
                    # Only use the mass calibration values from the first FOV in
                    # case the run is stopped prematurely and the values are not
                    # written out for subsequent FOVs.
                    if not param in calibration:
                        calibration[param] = np.float(item.attrib.get(param))
                fovs.append({
                    'run': run,
                    'folder': folder,
                    'dwell': float(item.attrib.get('AcquisitionTime')),
                    'scans': int(item.attrib.get('MaxNumberOfLevels', 1)),
                    'coordinates': coordinates,
                    'point_name': name,
                    'date': runtime,
                })
    return fovs, calibration
