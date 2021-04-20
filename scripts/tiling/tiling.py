""" Script for creating an FOV list json file that contains a grid of FOVs
generated from a single FOV json.
"""

import os
import json
import datetime
import argparse
import copy
import numpy as np

def tile(fov_list_json_file, xn, yn, overlap):
    ''' Using a template json file, creates another fov json that includes
    the tiled version of the original FOV.
    Args:
        fov_list_json_file: The FOV json containing the FOV to be tiled. The
            resulting tiled json is created in the same directory as this file.
        xn: The number of tiles in the x direction.
        yn: The number of tiles in the y direction.
        overlap: The degree of overlap between tiles. Must be between 0-1.
    '''

    with open(fov_list_json_file, 'r') as f:
        fov_list_single = json.load(f)
    dt = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    fov_list = {
        'exportDateTime': dt,
        'fovFormatVersion': fov_list_single['fovFormatVersion'],
        'fovs': []
    }

    fov_size = fov_list_single['fovs'][0]['fovSizeMicrons']
    x = fov_list_single['fovs'][0]['centerPointMicrons']['x']
    y = fov_list_single['fovs'][0]['centerPointMicrons']['y']
    overlap_microns = fov_size * overlap
    for xi in np.arange(xn):
        for yi in np.arange(yn):
            cur_x = x + xi * (fov_size - overlap_microns)
            cur_y = y + yi * (fov_size - overlap_microns)
            fov = copy.deepcopy(fov_list_single['fovs'][0])
            fov['centerPointMicrons']['x'] = cur_x
            fov['centerPointMicrons']['y'] = cur_y
            fov['name'] = f'row{yi}_col{xi}'
            fov_list['fovs'].append(fov)
    json_file_dest = os.path.join(
        os.path.dirname(fov_list_json_file), f'fov-list-{xn}x{yn}.json')
    with open(json_file_dest, 'w') as f:
        json.dump(fov_list, f, indent=4)


def get_parser(argv):
    ''' Generates the command line argument parser. '''
    parser = argparse.ArgumentParser(
        description='Generate an MIBIcontrol-importable FOV list json file that '
                    'contains a grid of FOVs. Example usage: \n'
                    'python tiling.py fov-list.json 5 5 0.1')
    parser.add_argument(
        'fov_list_json_file', type=str,
        help='The path to the fov-list.json file containing a single FOV that '
             'has been exported from MIBIcontrol. This script converts this '
             'json into a json file containing multiple fovs. The convention is'
             'that the top left FOV in the grid is at the same location as the '
             'single FOV in the original fov-list.json file.')
    parser.add_argument('xn', type=int, help='Number of FOVs in x-dir.')
    parser.add_argument('yn', type=int, help='Number of FOVs in y-dir.')
    parser.add_argument('overlap', type=float, help='Overlap between 0-1.')
    return parser

if __name__ == '__main__':
    args = get_parser().parse_args(sys.argv[1:])
    tile(**vars(args))
