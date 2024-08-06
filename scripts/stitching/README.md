# Stitiching
The [stitching.py](stitching.py) script is provided as a working example for
reconstructing multiple acquired FOVs into a single ROI, saving the combined
image as a MIBItiff file and optionally uploading the resulting image file to
MIBItracker.

## Requirements
- The `mibilib` conda environment has been created and activated or the required
packages have been installed to a Python environment. For details on installing
the `mibilib` conda environment, see the [README](../../README.md).
- The FOVs to stitch into a single ROI must have been acquired in the same run
and the run must have been acquired with the ROI acquisition feature introduced
with MIBIcontrol v1.9.1.

## Stitching a ROI
For a complete list of required and optional script arguments, please refer to
the [Usage](#usage) section.

The only required argument is the `--run_folder` which specifies the path to a
local folder which contains one or more ROIs to stitch. Note that all ROIs
contained in the folder will be reconstructed. When reconstructing a ROI from a
series of FOVs with this script, the `fov_name` metadata field of the MIBItiff
will be the name of the ROI, which is parsed from the file names in the local
folder.

`python .\stitching.py --run_folder /path/to/local/folder/`


Optionally, you can specify that the MIBItiff of the reconstructed ROI be saved
to a different location with the `--out_folder` argument.

`python .\stitching.py --run_folder /path/to/local/folder/ --out_folder /path/to/another/folder`

To upload the reconstructed ROI MIBItiff to MIBItracker, you must include
`--upload_to_mibitracker` and specify all of `--mibitracker_url`,
`--mibitracker_email`, and `--mibitracker_password`. Often, the URL, email, and
password are saved as environment variables.

`python .\stitching.py --run_folder /path/to/local/folder/ --upload_to_mibitracker --mibitracker_url https://sitename.api.ionpath.com --mibitracker_email you@email.com --mibitracker_password yourmibitrackerpassword`

When uploading to MIBItracker, the MIBItiff will be uploaded to the same run as
the run which acquired the ROI. The `fov_name` will be the name of the ROI,
which is parsed from the file names in the local folder.

If the ROI was acquired with overlap of adjacent FOVs or padding between
adjacent FOVs, use the `--fov_margin_size_x` and/or `--fov_margin_size_y`
arguments.

`python .\stitching.py --run_folder /path/to/local/folder/ --fov_margin_size_x 20 --fov_margin_size_y 10`

## Usage
Run `python stitching.py --help` to print out a list of required and optional
script arguments.

usage: `stitching.py [-h] [--run_folder RUN_FOLDER] [--out_folder OUT_FOLDER]
                    [--fov_margin_size_x FOV_MARGIN_SIZE_X]
                    [--fov_margin_size_y FOV_MARGIN_SIZE_Y]
                    [--upload_to_mibitracker]
                    [--mibitracker_url MIBITRACKER_URL]
                    [--mibitracker_email MIBITRACKER_EMAIL]
                    [--mibitracker_password MIBITRACKER_PASSWORD]
                    [--enforce_square]`

Script for creating a stitched ROI MIBItiff from a folder of FOVs. This script will take all tiled FOVs contained in --run_folder and stitch them into a single MIBItiff file. The output file will have the name [ROI_name].tiff and by default will be saved in the same folder as the individual FOV MIBItiffs. The output folder can be specified with the `--out_folder` argument. Additional arguments can be used to upload the resulting MIBItiff to MIBItracker as well as control the size and shape of the reconstructed image.

|||
|-|-|
|`-h`, `--help`|show this help message and exit|
|`--run_folder`|Local folder path with the original Run name and contents.|
|`--out_folder`|Local folder path to save the stitched MIBItiffs into.|
|`--fov_margin_size_x`|(optional) Sets the margin size in pixels for the x-dimension. Defaults to 0 for no overlap or spacing. Use a positive integer to add spacing between adjacent tiles and a negative integer to overlap adjacent tiles.|
|`--fov_margin_size_y`|(optional) Sets the margin size in pixels for the y-dimension. Defaults to 0 for no overlap or spacing. Use a positive integer to add spacing between adjacent tiles and a negative integer to overlap adjacent tiles.|
|`--upload_to_mibitracker`|Pass this flag to upload the resulting stitched MIBItiff to MIBItracker.|
|`--mibitracker_url`|(optional) MIBItracker backend URL if --upload_to_mibitracker if True (e.g. https://sitename.api.ionpath.com/).|
|`--mibitracker_email`|(optional) MIBItracker user name if --upload_to_mibitracker is True.|
|`--mibitracker_password`|(optional) MIBItracker password if --upload_to_mibitracker is True.|
|`--enforce_square`|Pass this flag to pad the stitched image with zeros so the resulting MIBItiff image is square.|

