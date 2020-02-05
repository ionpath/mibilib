"""Tests for mibidata.runs

Copyright (C) 2019 Ionpath, Inc.  All rights reserved.
"""

import os
import shutil
import tempfile
import unittest

from mibidata import runs

# Run calibration file.
XML = (
    '<DocRoot FileSystem="SAI">\n'
    '<Root RunTime="2016-03-21T15:03:27">\n'
    '<UserInfo UserName="Engineer" UserType="Engineer" />\n'
    '<Point PointName="Point">\n'
    '<RowNumber0 XAttrib="1000" YAttrib="2000" />\n'
    '<Chemical_Image XShift="0" XSize="2" YSize="2" EG6Active="false" '
    'MassGain="1." MassOffset="0." MassRange="200." TimeResolution="0.5" '
    'AcquisitionTime="4" >\n'
    '<Markers />\n'
    '</Chemical_Image>\n'
    '</Point>\n'
    '<Point PointName="Custom">\n'
    '<RowNumber0 XAttrib="-1000" YAttrib="-2000" />\n'
    '<Depth_Profile AcquisitionTime="0.2"  XSize="2" YSize="2"\n'
    'MassGain="1." MassOffset="0." MassRange="200." TimeResolution="0.5" \n'
    'MaxNumberOfLevels="2" >\n'
    '</Depth_Profile>\n'
    '</Point>\n'
    '</Root>\n'
    '</DocRoot>'
)


class TestRuns(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Write mass mml and run xml files to a temporary directory.
        cls.test_dir = tempfile.mkdtemp()

        cls.xml = os.path.join(cls.test_dir, 'run.xml')
        with open(cls.xml, 'w') as infile:
            infile.write(XML)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.test_dir)

    def test_parse_xml(self):

        expected_fovs = [
            {
                'run': 'run',
                'folder': os.path.join('Point1', 'RowNumber0',
                                       'Chemical_Image0'),
                'dwell': 4.0,
                'coordinates': (100, 200),
                'point_name': 'Point',
                'date': '2016-03-21T15:03:27',
                'scans': 1,
            },
            {
                'run': 'run',
                'folder': os.path.join('Point2', 'RowNumber0',
                                       'Depth_Profile0'),
                'dwell': 0.2,
                'coordinates': (-100, -200),
                'point_name': 'Custom',
                'date': '2016-03-21T15:03:27',
                'scans': 2,
            },
        ]
        expected_calibration = {
            'RasterStyle': None,
            'TimeResolution': 0.5,
            'MassGain': 1.0,
            'MassOffset': 0.0,
            'MassRange': 200.0,
            'XSize': 2.0,
            'YSize': 2.0
        }
        fovs, calibration = runs.parse_xml(self.xml)

        self.assertEqual(fovs, expected_fovs)
        self.assertEqual(calibration, expected_calibration)


if __name__ == '__main__':
    unittest.main()
