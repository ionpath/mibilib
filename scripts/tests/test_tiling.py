import os
import unittest
import tempfile
import json
import numpy as np
from tiling import tiling

FOV_LIST_JSON_ORIG = {
    "exportDateTime": "2020-09-04T15:13:58",
    "fovFormatVersion": "1.5",
    "fovs": [
        {
            "scanCount": 1,
            "centerPointMicrons": {
                "x": 123000.0,
                "y": 45000.0
            },
            "fovSizeMicrons": 800,
            "timingChoice": 1,
            "frameSizePixels": {
                "width": 64,
                "height": 64
            },
            "imagingPreset": {
                "preset": "Normal",
                "aperture": "2",
                "displayName": "Fine",
                "defaults": {
                    "timingChoice": 1
                }
            },
            "sectionId": 1,
            "slideId": 1,
            "name": "row0_col0",
            "notes": None,
            "timingDescription": "4 ms"
        }
    ]
}

FOV_LIST_JSON_TILED_EXPECTED = {
    "exportDateTime": "2020-09-04T15:13:58",
    "fovFormatVersion": "1.5",
    "fovs": [
        {
            "scanCount": 1,
            "centerPointMicrons": {
                "x": 123000.0,
                "y": 45000.0
            },
            "fovSizeMicrons": 800,
            "timingChoice": 1,
            "frameSizePixels": {
                "width": 64,
                "height": 64
            },
            "imagingPreset": {
                "preset": "Normal",
                "aperture": "2",
                "displayName": "Fine",
                "defaults": {
                    "timingChoice": 1
                }
            },
            "sectionId": 1,
            "slideId": 1,
            "name": "row0_col0",
            "notes": None,
            "timingDescription": "4 ms"
        },
        {
            "scanCount": 1,
            "centerPointMicrons": {
                "x": 123000.0,
                "y": 45720.0
            },
            "fovSizeMicrons": 800,
            "timingChoice": 1,
            "frameSizePixels": {
                "width": 64,
                "height": 64
            },
            "imagingPreset": {
                "preset": "Normal",
                "aperture": "2",
                "displayName": "Fine",
                "defaults": {
                    "timingChoice": 1
                }
            },
            "sectionId": 1,
            "slideId": 1,
            "name": "row1_col0",
            "notes": None,
            "timingDescription": "4 ms"
        },
        {
            "scanCount": 1,
            "centerPointMicrons": {
                "x": 123000.0,
                "y": 46440.0
            },
            "fovSizeMicrons": 800,
            "timingChoice": 1,
            "frameSizePixels": {
                "width": 64,
                "height": 64
            },
            "imagingPreset": {
                "preset": "Normal",
                "aperture": "2",
                "displayName": "Fine",
                "defaults": {
                    "timingChoice": 1
                }
            },
            "sectionId": 1,
            "slideId": 1,
            "name": "row2_col0",
            "notes": None,
            "timingDescription": "4 ms"
        },
        {
            "scanCount": 1,
            "centerPointMicrons": {
                "x": 123000.0,
                "y": 47160.0
            },
            "fovSizeMicrons": 800,
            "timingChoice": 1,
            "frameSizePixels": {
                "width": 64,
                "height": 64
            },
            "imagingPreset": {
                "preset": "Normal",
                "aperture": "2",
                "displayName": "Fine",
                "defaults": {
                    "timingChoice": 1
                }
            },
            "sectionId": 1,
            "slideId": 1,
            "name": "row3_col0",
            "notes": None,
            "timingDescription": "4 ms"
        },
        {
            "scanCount": 1,
            "centerPointMicrons": {
                "x": 123000.0,
                "y": 47880.0
            },
            "fovSizeMicrons": 800,
            "timingChoice": 1,
            "frameSizePixels": {
                "width": 64,
                "height": 64
            },
            "imagingPreset": {
                "preset": "Normal",
                "aperture": "2",
                "displayName": "Fine",
                "defaults": {
                    "timingChoice": 1
                }
            },
            "sectionId": 1,
            "slideId": 1,
            "name": "row4_col0",
            "notes": None,
            "timingDescription": "4 ms"
        },
        {
            "scanCount": 1,
            "centerPointMicrons": {
                "x": 123720.0,
                "y": 45000.0
            },
            "fovSizeMicrons": 800,
            "timingChoice": 1,
            "frameSizePixels": {
                "width": 64,
                "height": 64
            },
            "imagingPreset": {
                "preset": "Normal",
                "aperture": "2",
                "displayName": "Fine",
                "defaults": {
                    "timingChoice": 1
                }
            },
            "sectionId": 1,
            "slideId": 1,
            "name": "row0_col1",
            "notes": None,
            "timingDescription": "4 ms"
        },
        {
            "scanCount": 1,
            "centerPointMicrons": {
                "x": 123720.0,
                "y": 45720.0
            },
            "fovSizeMicrons": 800,
            "timingChoice": 1,
            "frameSizePixels": {
                "width": 64,
                "height": 64
            },
            "imagingPreset": {
                "preset": "Normal",
                "aperture": "2",
                "displayName": "Fine",
                "defaults": {
                    "timingChoice": 1
                }
            },
            "sectionId": 1,
            "slideId": 1,
            "name": "row1_col1",
            "notes": None,
            "timingDescription": "4 ms"
        },
        {
            "scanCount": 1,
            "centerPointMicrons": {
                "x": 123720.0,
                "y": 46440.0
            },
            "fovSizeMicrons": 800,
            "timingChoice": 1,
            "frameSizePixels": {
                "width": 64,
                "height": 64
            },
            "imagingPreset": {
                "preset": "Normal",
                "aperture": "2",
                "displayName": "Fine",
                "defaults": {
                    "timingChoice": 1
                }
            },
            "sectionId": 1,
            "slideId": 1,
            "name": "row2_col1",
            "notes": None,
            "timingDescription": "4 ms"
        },
        {
            "scanCount": 1,
            "centerPointMicrons": {
                "x": 123720.0,
                "y": 47160.0
            },
            "fovSizeMicrons": 800,
            "timingChoice": 1,
            "frameSizePixels": {
                "width": 64,
                "height": 64
            },
            "imagingPreset": {
                "preset": "Normal",
                "aperture": "2",
                "displayName": "Fine",
                "defaults": {
                    "timingChoice": 1
                }
            },
            "sectionId": 1,
            "slideId": 1,
            "name": "row3_col1",
            "notes": None,
            "timingDescription": "4 ms"
        },
        {
            "scanCount": 1,
            "centerPointMicrons": {
                "x": 123720.0,
                "y": 47880.0
            },
            "fovSizeMicrons": 800,
            "timingChoice": 1,
            "frameSizePixels": {
                "width": 64,
                "height": 64
            },
            "imagingPreset": {
                "preset": "Normal",
                "aperture": "2",
                "displayName": "Fine",
                "defaults": {
                    "timingChoice": 1
                }
            },
            "sectionId": 1,
            "slideId": 1,
            "name": "row4_col1",
            "notes": None,
            "timingDescription": "4 ms"
        },
        {
            "scanCount": 1,
            "centerPointMicrons": {
                "x": 124440.0,
                "y": 45000.0
            },
            "fovSizeMicrons": 800,
            "timingChoice": 1,
            "frameSizePixels": {
                "width": 64,
                "height": 64
            },
            "imagingPreset": {
                "preset": "Normal",
                "aperture": "2",
                "displayName": "Fine",
                "defaults": {
                    "timingChoice": 1
                }
            },
            "sectionId": 1,
            "slideId": 1,
            "name": "row0_col2",
            "notes": None,
            "timingDescription": "4 ms"
        },
        {
            "scanCount": 1,
            "centerPointMicrons": {
                "x": 124440.0,
                "y": 45720.0
            },
            "fovSizeMicrons": 800,
            "timingChoice": 1,
            "frameSizePixels": {
                "width": 64,
                "height": 64
            },
            "imagingPreset": {
                "preset": "Normal",
                "aperture": "2",
                "displayName": "Fine",
                "defaults": {
                    "timingChoice": 1
                }
            },
            "sectionId": 1,
            "slideId": 1,
            "name": "row1_col2",
            "notes": None,
            "timingDescription": "4 ms"
        },
        {
            "scanCount": 1,
            "centerPointMicrons": {
                "x": 124440.0,
                "y": 46440.0
            },
            "fovSizeMicrons": 800,
            "timingChoice": 1,
            "frameSizePixels": {
                "width": 64,
                "height": 64
            },
            "imagingPreset": {
                "preset": "Normal",
                "aperture": "2",
                "displayName": "Fine",
                "defaults": {
                    "timingChoice": 1
                }
            },
            "sectionId": 1,
            "slideId": 1,
            "name": "row2_col2",
            "notes": None,
            "timingDescription": "4 ms"
        },
        {
            "scanCount": 1,
            "centerPointMicrons": {
                "x": 124440.0,
                "y": 47160.0
            },
            "fovSizeMicrons": 800,
            "timingChoice": 1,
            "frameSizePixels": {
                "width": 64,
                "height": 64
            },
            "imagingPreset": {
                "preset": "Normal",
                "aperture": "2",
                "displayName": "Fine",
                "defaults": {
                    "timingChoice": 1
                }
            },
            "sectionId": 1,
            "slideId": 1,
            "name": "row3_col2",
            "notes": None,
            "timingDescription": "4 ms"
        },
        {
            "scanCount": 1,
            "centerPointMicrons": {
                "x": 124440.0,
                "y": 47880.0
            },
            "fovSizeMicrons": 800,
            "timingChoice": 1,
            "frameSizePixels": {
                "width": 64,
                "height": 64
            },
            "imagingPreset": {
                "preset": "Normal",
                "aperture": "2",
                "displayName": "Fine",
                "defaults": {
                    "timingChoice": 1
                }
            },
            "sectionId": 1,
            "slideId": 1,
            "name": "row4_col2",
            "notes": None,
            "timingDescription": "4 ms"
        },
        {
            "scanCount": 1,
            "centerPointMicrons": {
                "x": 125160.0,
                "y": 45000.0
            },
            "fovSizeMicrons": 800,
            "timingChoice": 1,
            "frameSizePixels": {
                "width": 64,
                "height": 64
            },
            "imagingPreset": {
                "preset": "Normal",
                "aperture": "2",
                "displayName": "Fine",
                "defaults": {
                    "timingChoice": 1
                }
            },
            "sectionId": 1,
            "slideId": 1,
            "name": "row0_col3",
            "notes": None,
            "timingDescription": "4 ms"
        },
        {
            "scanCount": 1,
            "centerPointMicrons": {
                "x": 125160.0,
                "y": 45720.0
            },
            "fovSizeMicrons": 800,
            "timingChoice": 1,
            "frameSizePixels": {
                "width": 64,
                "height": 64
            },
            "imagingPreset": {
                "preset": "Normal",
                "aperture": "2",
                "displayName": "Fine",
                "defaults": {
                    "timingChoice": 1
                }
            },
            "sectionId": 1,
            "slideId": 1,
            "name": "row1_col3",
            "notes": None,
            "timingDescription": "4 ms"
        },
        {
            "scanCount": 1,
            "centerPointMicrons": {
                "x": 125160.0,
                "y": 46440.0
            },
            "fovSizeMicrons": 800,
            "timingChoice": 1,
            "frameSizePixels": {
                "width": 64,
                "height": 64
            },
            "imagingPreset": {
                "preset": "Normal",
                "aperture": "2",
                "displayName": "Fine",
                "defaults": {
                    "timingChoice": 1
                }
            },
            "sectionId": 1,
            "slideId": 1,
            "name": "row2_col3",
            "notes": None,
            "timingDescription": "4 ms"
        },
        {
            "scanCount": 1,
            "centerPointMicrons": {
                "x": 125160.0,
                "y": 47160.0
            },
            "fovSizeMicrons": 800,
            "timingChoice": 1,
            "frameSizePixels": {
                "width": 64,
                "height": 64
            },
            "imagingPreset": {
                "preset": "Normal",
                "aperture": "2",
                "displayName": "Fine",
                "defaults": {
                    "timingChoice": 1
                }
            },
            "sectionId": 1,
            "slideId": 1,
            "name": "row3_col3",
            "notes": None,
            "timingDescription": "4 ms"
        },
        {
            "scanCount": 1,
            "centerPointMicrons": {
                "x": 125160.0,
                "y": 47880.0
            },
            "fovSizeMicrons": 800,
            "timingChoice": 1,
            "frameSizePixels": {
                "width": 64,
                "height": 64
            },
            "imagingPreset": {
                "preset": "Normal",
                "aperture": "2",
                "displayName": "Fine",
                "defaults": {
                    "timingChoice": 1
                }
            },
            "sectionId": 1,
            "slideId": 1,
            "name": "row4_col3",
            "notes": None,
            "timingDescription": "4 ms"
        },
        {
            "scanCount": 1,
            "centerPointMicrons": {
                "x": 125880.0,
                "y": 45000.0
            },
            "fovSizeMicrons": 800,
            "timingChoice": 1,
            "frameSizePixels": {
                "width": 64,
                "height": 64
            },
            "imagingPreset": {
                "preset": "Normal",
                "aperture": "2",
                "displayName": "Fine",
                "defaults": {
                    "timingChoice": 1
                }
            },
            "sectionId": 1,
            "slideId": 1,
            "name": "row0_col4",
            "notes": None,
            "timingDescription": "4 ms"
        },
        {
            "scanCount": 1,
            "centerPointMicrons": {
                "x": 125880.0,
                "y": 45720.0
            },
            "fovSizeMicrons": 800,
            "timingChoice": 1,
            "frameSizePixels": {
                "width": 64,
                "height": 64
            },
            "imagingPreset": {
                "preset": "Normal",
                "aperture": "2",
                "displayName": "Fine",
                "defaults": {
                    "timingChoice": 1
                }
            },
            "sectionId": 1,
            "slideId": 1,
            "name": "row1_col4",
            "notes": None,
            "timingDescription": "4 ms"
        },
        {
            "scanCount": 1,
            "centerPointMicrons": {
                "x": 125880.0,
                "y": 46440.0
            },
            "fovSizeMicrons": 800,
            "timingChoice": 1,
            "frameSizePixels": {
                "width": 64,
                "height": 64
            },
            "imagingPreset": {
                "preset": "Normal",
                "aperture": "2",
                "displayName": "Fine",
                "defaults": {
                    "timingChoice": 1
                }
            },
            "sectionId": 1,
            "slideId": 1,
            "name": "row2_col4",
            "notes": None,
            "timingDescription": "4 ms"
        },
        {
            "scanCount": 1,
            "centerPointMicrons": {
                "x": 125880.0,
                "y": 47160.0
            },
            "fovSizeMicrons": 800,
            "timingChoice": 1,
            "frameSizePixels": {
                "width": 64,
                "height": 64
            },
            "imagingPreset": {
                "preset": "Normal",
                "aperture": "2",
                "displayName": "Fine",
                "defaults": {
                    "timingChoice": 1
                }
            },
            "sectionId": 1,
            "slideId": 1,
            "name": "row3_col4",
            "notes": None,
            "timingDescription": "4 ms"
        },
        {
            "scanCount": 1,
            "centerPointMicrons": {
                "x": 125880.0,
                "y": 47880.0
            },
            "fovSizeMicrons": 800,
            "timingChoice": 1,
            "frameSizePixels": {
                "width": 64,
                "height": 64
            },
            "imagingPreset": {
                "preset": "Normal",
                "aperture": "2",
                "displayName": "Fine",
                "defaults": {
                    "timingChoice": 1
                }
            },
            "sectionId": 1,
            "slideId": 1,
            "name": "row4_col4",
            "notes": None,
            "timingDescription": "4 ms"
        }
    ]
}

class TestTiling(unittest.TestCase):
    def test_tile(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fov_list_file = os.path.join(tmpdir, 'fov-list.json')
            with open(fov_list_file, 'w') as f:
                json.dump(FOV_LIST_JSON_ORIG, f)
            tiling.tile(fov_list_file, 5, 5, 0.1)
            fov_list_file_tiled = os.path.join(tmpdir, 'fov-list-5x5.json')
            with open(fov_list_file_tiled, 'r') as f:
                fov_list_json_tiled_actual = json.load(f)
            np.testing.assert_array_equal(
                fov_list_json_tiled_actual['fovs'],
                FOV_LIST_JSON_TILED_EXPECTED['fovs'])