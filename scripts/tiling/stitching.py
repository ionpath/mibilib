""" Script for creating a stitched ROI MIBItiff from a folder of FOVs
"""

import numpy as np
import os
from mibidata import mibi_image as mi
from mibitracker.request_helpers import MibiRequests
from collections import OrderedDict
import time
from mibidata import tiff
import json

MAX_TRIES = 10


def combine_entity_by_name(roi_fov_paths, cols, rows, enforce_square):
    min_col = np.min(cols)
    min_row = np.min(rows)
    cols=[v-min_col+1 for v in cols]
    rows=[v-min_row+1 for v in rows]
    w = np.max(cols)
    h = np.max(rows)

    panel = None
    out_img = None
    for fov_i,roi_fov_path in enumerate(roi_fov_paths):
        print(fov_i+1,roi_fov_path)

        fov_img = tiff.read(roi_fov_path)
        panel = fov_img.channels
        fov_img = fov_img.data

        img_shape = list(np.shape(fov_img))
        ch_count = np.min(img_shape)
        shape_2d = img_shape[:-1]

        if out_img is None:
            out_img = np.zeros((h*shape_2d[0], w*shape_2d[1], ch_count), dtype=fov_img.dtype)
            out_img_shape = list(np.shape(out_img))

        for ch_i in range(ch_count):
            out_img[((rows[fov_i]-1)*shape_2d[0]):(rows[fov_i]*shape_2d[0]), 
                    ((cols[fov_i]-1)*shape_2d[1]):(cols[fov_i]*shape_2d[1]), ch_i] = fov_img[:,:,ch_i]
    
    if enforce_square:
        if out_img_shape[0] > out_img_shape[1]:
            out_img = np.pad(out_img,((0,0),(0,out_img_shape[0]-out_img_shape[1]),(0,0)))
        elif out_img_shape[0] < out_img_shape[1]:
            out_img = np.pad(out_img,((0,out_img_shape[1]-out_img_shape[0]),(0,0),(0,0)))
        
    return out_img.astype(out_img.dtype, copy=False), panel, int(max(w*shape_2d[1], h*shape_2d[0]))


def run_task(fov_paths, out_path, session_dict, mt_upload):
    unique_rois = np.unique([os.path.basename(p).split("-")[-1].split(".tiff")[0].split("_")[0] for p in fov_paths])
    roi_path_groups = dict([(u,[p for p in fov_paths if u in p]) for u in unique_rois])
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

    for roi,roi_fov_paths in roi_path_groups.items():
        print(roi)

        cols = []
        rows = []
        for fov_path in roi_fov_paths:
            fov_name = os.path.basename(fov_path).split("-")[-1].split(".tiff")[0]
            c, r = fov_name.split("_")[1:]
            cols.append(int(c[1:].lstrip("0")))
            rows.append(int(r[1:].lstrip("0")))

        out_img, panel, max_dim = combine_entity_by_name(roi_fov_paths, cols, rows, enforce_square=True)
        out_img = out_img.astype(np.uint8, copy=False)

        um_min_x, um_min_y = 999999999, 999999999
        for fov_path in roi_fov_paths:
            
            json_file = os.path.dirname(fov_path)+"/"+"-".join(os.path.basename(fov_path).split("-")[:2])+"-scan-1.json"
            with open(json_file) as f:
                bin_json = json.load(f)
                coord = bin_json["coordinates"]
                if coord["x"] < um_min_x:
                    um_min_x = coord["x"]
                if coord["y"] < um_min_y:
                    um_min_y = coord["y"]

        run = os.path.basename(os.path.dirname(roi_fov_paths[0]))
        fov = "FOV"+os.path.basename(roi_fov_paths[0]).split("-")[1]
        print(run, fov)
        
        for t in range(MAX_TRIES):
            try:
                try:
                    ref_image_id = mr.image_id(run, fov)
                except:
                    ref_image_id = mr.image_id(run, fov.replace("V0", "V"))
                break
            except:
                if t < MAX_TRIES-1:
                    time.sleep(0.50)
                else:
                    try:
                        ref_image_id = mr.image_id(run, fov)
                    except:
                        ref_image_id = mr.image_id(run, fov.replace("V0", "V"))
        
        for t in range(MAX_TRIES):
            try:
                ref_json = mr.get('images/{}/'.format(ref_image_id)).json()
                break
            except:
                if t < MAX_TRIES-1:
                    time.sleep(0.50)
                else:
                    ref_json = mr.get('images/{}/'.format(ref_image_id)).json()

        sample_id = run+"__"+roi
        f_split = ref_json['folder'].split('/')
        f_split[0] = sample_id
        folder_name = '/'.join(f_split[:3])

        px_per_u = ref_json["frame"]/ref_json["fov_size"]

        metadata = {
            'run': '{}'.format(ref_json['run']['label']),
            'date': ref_json['run']['run_date'],
            'coordinates': (um_min_x, um_min_y),
            'size': max_dim/px_per_u,  # issue: assumption that w==h doens't hold
            'slide': ref_json['section']['slide']['id'],
            'fov_name': sample_id,
            'frame': max_dim,  # issue: assumption that w==h doens't hold
            'folder': folder_name,
            'fov_id': f_split[0],
            # assumption that all fovs are same
            'dwell': ref_json['dwell_time'],
            'scans': ','.join([str(d) for d in range(ref_json['depths'])]),
            # assumption that all fovs are same
            'aperture': ref_json['run']['aperture']['label'],
            'instrument': ref_json['run']['instrument']['name'],
            'tissue': ref_json['formatted_tissue'],
            'panel': ref_json['section']['panel']['name'],
            'version': 'alpha',
            # assumption that all fovs are same
            'mass_offset': ref_json['mass_offset'],
            # assumption that all fovs are same
            'mass_gain': ref_json['mass_gain'],
            # assumption that all fovs are same
            'time_resolution': ref_json['time_bin'],
            'filename': '{}'.format(ref_json['run']['name'])
        }

        out_mibi_tiff = mi.MibiImage(
            out_img, panel, datetime_format='%Y-%m-%d', **metadata)

        f_split = out_mibi_tiff.folder.split('/')
        f_split[0] = sample_id
        out_mibi_tiff.set_fov_id(f_split[0], '/'.join(f_split))

        tiff.write(out_path, out_mibi_tiff, dtype=np.float32)
        print(f"Stitched MIBItiff saved to {out_path}.")

        if mt_upload:
            for t in range(MAX_TRIES):
                try:
                    exists = mr.get(
                        '/images/', params={'run__label': ref_json['run']['label'], 'number': f_split[0]}).json()
                    break
                except:
                    if t < MAX_TRIES-1:
                        time.sleep(0.50)
                    else:
                        exists = mr.get(
                            '/images/', params={'run__label': ref_json['run']['label'], 'number': f_split[0]}).json()

            full_id = exists['results'][0]['id'] if exists['count'] else None

            if not full_id:
                new_im_metadata = {}
                new_im_metadata['run'] = ref_json['run']['id']
                new_im_metadata['point'] = sample_id
                new_im_metadata['number'] = out_mibi_tiff.fov_id
                new_im_metadata['folder'] = out_mibi_tiff.folder
                new_im_metadata['fov_size'] = max_dim/px_per_u
                # assumption that all fovs are same
                new_im_metadata['dwell_time'] = ref_json['dwell_time']
                # assumption that all fovs are same
                new_im_metadata['depths'] = ref_json['depths']
                new_im_metadata['frame'] = max_dim
                # assumption that all fovs are same
                new_im_metadata['time_bin'] = ref_json['time_bin']
                # assumption that all fovs are same
                new_im_metadata['mass_gain'] = ref_json['mass_gain']
                # assumption that all fovs are same
                new_im_metadata['mass_offset'] = ref_json['mass_offset']
                new_im_metadata['x_coord'] = int(np.round(um_min_x))
                new_im_metadata['y_coord'] = int(np.round(um_min_y))
                new_im_metadata['tissue'] = \
                    ref_json['tissue'] and ref_json['tissue']['id']
                new_im_metadata['section'] = ref_json['section']['id']
                # assumption that all fovs are same
                new_im_metadata['aperture'] = ref_json['aperture']['id']
                # assumption that all fovs are same
                new_im_metadata['imaging_preset'] = ref_json['imaging_preset']
                # assumption that all fovs are same
                new_im_metadata['lens1_voltage'] = ref_json['lens1_voltage']

                for t in range(MAX_TRIES):
                    try:
                        _ = mr.post('/images/', json=new_im_metadata)
                        break
                    except:
                        if t < MAX_TRIES-1:
                            time.sleep(0.50)
                        else:
                            _ = mr.post('/images/', json=new_im_metadata)

            for t in range(MAX_TRIES):
                try:
                    mr.upload_mibitiff(out_path, run_id=ref_json['run']['id'])
                    break
                except:
                    if t < MAX_TRIES-1:
                        time.sleep(0.50)
                    else:
                        mr.upload_mibitiff(out_path, run_id=ref_json['run']['id'])
            
            print(f"Stitched MIBItiff, {out_path} uploaded to MIBItracker.")
                        

if __name__ == "__main__":

    fovs_folder = "/Users/mnagy/projects/stitch_script_test/2024-04-29T10-07-46_gold_tonsil_3x3_coarse_ROI"
    out_path = "/Users/mnagy/projects/stitch_script_test/2024-04-29T10-07-46_gold_tonsil_3x3_coarse_ROI.tiff"
    cmd = f'ls {fovs_folder}/*.tiff'
    fov_paths = os.popen(cmd).read().strip().split("\n")
    try:
        fov_paths.remove("")
    except:
        pass

    session_dict = {
        "url": "https://mibitracker.api.ionpath.com/",  # MIBItracker backend URL
        "email": "",  # User name
        "password": ""  # User password
    }
    mt_upload = True

    run_task(fov_paths, out_path, session_dict, mt_upload)

