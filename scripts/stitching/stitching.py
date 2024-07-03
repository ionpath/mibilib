""" Script for creating a stitched ROI MIBItiff from a folder of FOVs.
"""

import argparse
import json
import os
import sys
import time

import numpy as np

from mibidata import mibi_image as mi
from mibidata import tiff
from mibitracker.request_helpers import MibiRequests

MAX_TRIES = 5

def combine_entity_by_name(roi_fov_paths, cols, rows, enforce_square, margin):
    min_col = np.min(cols)
    min_row = np.min(rows)
    cols=[v-min_col+1 for v in cols]
    rows=[v-min_row+1 for v in rows]
    w = np.max(cols)
    h = np.max(rows)

    panel = None
    out_img = None
    ref_metadata = None
    for fov_i,roi_fov_path in enumerate(roi_fov_paths):
        fov_img = tiff.read(roi_fov_path)
        panel = fov_img.channels
        fov_img = fov_img.data
        if ref_metadata is None:
            ref_metadata = tiff.info(roi_fov_path)

        img_shape = list(np.shape(fov_img))
        ch_count = np.min(img_shape)
        shape_2d = img_shape[:-1]

        if out_img is None:
            out_img = np.zeros(
                (h*shape_2d[0]+(h-1)*margin["y"], 
                 w*shape_2d[1]+(w-1)*margin["x"], ch_count),
                 dtype=fov_img.dtype)
            out_img_shape = list(np.shape(out_img))

        out_img[((rows[fov_i]-1)*shape_2d[0]+(rows[fov_i]-1)*margin["y"]):
                (rows[fov_i]*shape_2d[0]+(rows[fov_i]-1)*margin["y"]), 
                ((cols[fov_i]-1)*shape_2d[1]+(cols[fov_i]-1)*margin["x"]):
                (cols[fov_i]*shape_2d[1]+(cols[fov_i]-1)*margin["x"]), :] = \
                    fov_img[:,:,:]
    
    if enforce_square:
        if out_img_shape[0] > out_img_shape[1]:
            out_img = np.pad(
                out_img,((0,0),(0,out_img_shape[0]-out_img_shape[1]),(0,0)))
        elif out_img_shape[0] < out_img_shape[1]:
            out_img = np.pad(
                out_img,((0,out_img_shape[1]-out_img_shape[0]),(0,0),(0,0)))
        
    return out_img.astype(out_img.dtype, copy=False), panel, \
        int(max(w*shape_2d[1], h*shape_2d[0])), ref_metadata


def stitch_fovs(run_folder, out_folder, session_dict, upload_to_mibitracker,
                fov_margin_size, enforce_square):
    run = os.path.basename(run_folder)
    run_json_file = os.path.join(run_folder,run)+".json"
    with open(run_json_file) as rf:
        run_json = json.load(rf)
    for r in run_json["rois"]:
        if r["standardTarget"] in ["Auto Gain"]:
            continue
        roi = r["name"]
        px_per_u = r["frameSizePixels"]["width"] / r["fovSizeMicrons"]
        margin = fov_margin_size
        if margin is None:
            margin = {
                "x":int(np.round(r["xMargin"]*px_per_u)),
                "y":int(np.round(r["yMargin"]*px_per_u))
            }
        elif type(margin) != dict:
            if type(margin) != list:
                margin = {"x":margin, "y":margin}
            else:
                margin = {"x":margin[0], "y":margin[1]}
        cols, rows = [], []
        um_min_x, um_min_y = 999999999, 999999999
        roi_fov_paths=[]
        for f in r["fovs"]:
            fov_name = f["name"]
            cols.append(f["gridPosition"]["x"]+1)
            rows.append(f["gridPosition"]["y"]+1)
            coord = f["centerPointMicrons"]
            if coord["x"] < um_min_x:
                um_min_x = coord["x"]
            if coord["y"] < um_min_y:
                um_min_y = coord["y"]
            roi_fov_paths.append(
                os.path.join(
                    run_folder,
                    "fov" + "-" + str(
                        f["runOrder"]).zfill(2) + "-" + fov_name) + ".tiff")
    
        print(f'Stitching {run} - {roi}: {len(roi_fov_paths)} FOVs')
        out_img, panel, max_dim, ref_metadata = combine_entity_by_name(
            roi_fov_paths, cols, rows, enforce_square=enforce_square,
            margin=margin)
        out_img = out_img.astype(np.uint8, copy=False)

        metadata = ref_metadata.copy()
        metadata["coordinates"] = (um_min_x, um_min_y)
        metadata["size"] = max_dim/px_per_u
        metadata["fov_name"] = roi

        out_mibi_tiff = mi.MibiImage(
            out_img, panel, datetime_format='%Y-%m-%d', **metadata)
        
        f_split = out_mibi_tiff.folder.split('/')
        f_split[0] = roi
        out_mibi_tiff.set_fov_id(f_split[0], '/'.join(f_split))

        if not out_folder:
            out_path = os.path.join(run_folder, roi + ".tiff")
        else:
            out_path = os.path.join(out_folder,roi+".tiff")
        tiff.write(out_path, out_mibi_tiff, dtype=np.float32)
        print(f"Stitched MIBItiff saved to {out_path}.")

        if upload_to_mibitracker:
            mr = None
            for t in range(MAX_TRIES):
                try:
                    mr = MibiRequests(**session_dict)
                    break
                except:
                    if t < MAX_TRIES-1:
                        time.sleep(0.50)
                    else:
                        mr = MibiRequests(**session_dict)
            for t in range(MAX_TRIES):
                try:
                    exists = mr.get(
                        '/images/',
                        params={
                            'run__label': run,
                            'number': f_split[0]}).json()
                    break
                except:
                    if t < MAX_TRIES-1:
                        time.sleep(0.50)
                    else:
                        exists = mr.get(
                            '/images/',
                            params={
                                'run__label': run,
                                'number': f_split[0]}).json()

            full_id = exists['results'][0]['id'] if exists['count'] \
                else None

            for t in range(MAX_TRIES):
                try:
                    run_id = mr.get(
                        '/runs/',
                        params={'name': run}).json()['results'][0]['id']
                    break
                except:
                    if t < MAX_TRIES-1:
                        time.sleep(0.50)
                    else:
                        run_id = mr.get(
                            '/runs/',
                            params={'name': run}).json()['results'][0]['id']

            new_im_metadata = {}
            new_im_metadata['run'] = run_id
            new_im_metadata['point'] = roi
            new_im_metadata['number'] = out_mibi_tiff.fov_id
            new_im_metadata['folder'] = out_mibi_tiff.folder
            new_im_metadata['fov_size'] = max_dim/px_per_u
            new_im_metadata['dwell_time'] = metadata['dwell']
            new_im_metadata['depths'] = metadata['scans']
            new_im_metadata['frame'] = max_dim
            new_im_metadata['time_bin'] = metadata['time_resolution']
            new_im_metadata['mass_gain'] = metadata['mass_gain']
            new_im_metadata['mass_offset'] = metadata['mass_offset']
            new_im_metadata['x_coord'] = int(np.round(um_min_x))
            new_im_metadata['y_coord'] = int(np.round(um_min_y))
            new_im_metadata['tissue'] = metadata['raw_description']['fov'] \
                ['section']['tissue'] and metadata['raw_description'] \
                    ['fov']['section']['tissue']['id']
            new_im_metadata['section'] = metadata['raw_description'] \
                ['fov']['section']['id']
            new_im_metadata['aperture'] = metadata['aperture']
            new_im_metadata['imaging_preset'] = metadata['imaging_preset']
            new_im_metadata['lens1_voltage'] = metadata['lens1_voltage']

            if not full_id:
                for t in range(MAX_TRIES):
                    try:
                        mr.post('/images/', json=new_im_metadata)
                        break
                    except:
                        if t < MAX_TRIES-1:
                            time.sleep(0.50)
                        else:
                            _ = mr.post('/images/', json=new_im_metadata)
            else:
                for t in range(MAX_TRIES):
                    try:
                        mr.put(f'/images/{full_id}', json=new_im_metadata)
                        break
                    except:
                        if t < MAX_TRIES-1:
                            time.sleep(0.50)
                        else:
                            mr.put(
                                f'/images/{full_id}', json=new_im_metadata)

            for t in range(MAX_TRIES):
                try:
                    mr.upload_mibitiff(out_path, run_id=run_id)
                    break
                except:
                    if t < MAX_TRIES-1:
                        time.sleep(0.50)
                    else:
                        mr.upload_mibitiff(out_path, run_id=run_id)
            
            print(
                f"Stitched MIBItiff, {out_path}, uploaded to MIBItracker.")

def parse_args(args):
    ''' Argument parsing helper function.   
    '''
    parser = argparse.ArgumentParser(
        description='Script for creating a stitched ROI MIBItiff from a folder '
                    'of FOVs. This script will take all tiled FOVs contained '
                    'in --run_folder and stitch them into a single MIBItiff '
                    'file. The output file will have the name [ROI_name].tiff '
                    'and by default will be saved in the same folder as the '
                    'individual FOV MIBItiffs. The output folder can be '
                    'specified with the --out_folder argument. Additional '
                    'arguments can be used to upload the resulting MIBItiff to '
                    'MIBItracker as well as control the size and shape of the '
                    'reconstructed image.',
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument(
        '--run_folder',
        help='Local folder path with the original Run name and contents.')
    parser.add_argument(
        '--out_folder', required=False,
        help='Local folder path to save the stitched MIBItiffs into.')
    parser.add_argument(
        '--fov_margin_size_x', type=int, required=False, default=0,
        help='(optional) Sets the margin size in pixels for the x-dimension. '
             'Defaults to 0 for no overlap or spacing. Use a positive integer '
             'to add spacing between adjacent tiles and a negative integer to '
             'overlap adjacent tiles.')
    parser.add_argument(
        '--fov_margin_size_y', type=int, required=False, default=0,
        help='(optional) Sets the margin size in pixels for the y-dimension. '
             'Defaults to 0 for no overlap or spacing. Use a positive integer '
             'to add spacing between adjacent tiles and a negative integer to '
             'overlap adjacent tiles.')
    parser.add_argument(
        '--upload_to_mibitracker', action='store_true',
        help='Pass this flag to upload the resulting stitched MIBItiff to '
             'MIBItracker.')
    parser.add_argument(
        '--mibitracker_url', required=False,
        help='(optional) MIBItracker backend URL if --upload_to_mibitracker if '
             'True (e.g. https://sitename.api.ionpath.com/).')
    parser.add_argument(
        '--mibitracker_email', required=False,
        help='(optional) MIBItracker user name if --upload_to_mibitracker is '
             'True.')
    parser.add_argument(
        '--mibitracker_password', required=False,
        help='(optional) MIBItracker password if --upload_to_mibitracker is '
             'True.')
    parser.add_argument(
        '--enforce_square', action='store_true',
        help='Pass this flag to pad the stitched image with zeros so the '
             'resulting MIBItiff image is square.')

    args = parser.parse_args(args)

    # Check that required arguments are included
    if not args.run_folder:
        raise ValueError(
            '--run_folder is a required argument and must be specified')
    # If uploading to MIBItracker, check that URL, email, and password are
    # included.
    if args.upload_to_mibitracker and not all(
        [args.mibitracker_url, args.mibitracker_email,
         args.mibitracker_password]):
        raise ValueError(
            '--mibitracker_url, --mibitracker_email, and '
            '--mibitracker_password must be specified if '
            '--upload_to_mibitracker is `True`.')
    # Properly set the dict with the x- and y-margins
    if not args.fov_margin_size_x and args.fov_margin_size_y:
        args.fov_margin_size = None
    else:
        args.fov_margin_size = {
            'x': args.fov_margin_size_x if args.fov_margin_size_x else 0,
            'y': args.fov_margin_size_y if args.fov_margin_size_y else 0,
        }

    return args

if __name__ == "__main__":
    args = parse_args(sys.argv[1:])

    session_dict = {
        'url': args.mibitracker_url,
        'email': args.mibitracker_email,
        'password': args.mibitracker_password
    }

    stitch_fovs(args.run_folder, args.out_folder, session_dict,
                args.upload_to_mibitracker, args.fov_margin_size,
                args.enforce_square)
