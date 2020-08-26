[![CircleCI](https://circleci.com/gh/ionpath/mibilib.svg?style=svg&circle-token=e798611a4abf9f2503a532c8ad5fd02d849d85a0)](https://circleci.com/gh/ionpath/mibilib)

# mibilib

Python client for IONpath MIBItracker API, plus utility functions for working
with MIBItiff images.

https://ionpath.github.io/mibilib/

## Setup

### Install Python 3.7
Install the Python 3.7 version of [Miniconda](https://conda.io/miniconda.html).
Even if your system already has a version of Python installed, it is strongly
recommended to use the `conda` environment manager to install and manage this
library's dependencies.

### Option A (Development): Clone repository and create environment
This option downloads the source code and creates a development environment. It does not add this library to the path, so if your use case is to import it into
other projects rather than interact with the source, Option B is recommended.
```bash
cd <path/to/where/you/want/to/install/project>
git clone https://github.com/ionpath/mibilib
cd mibilib
```

```bash
conda env create -f environment.yml
conda activate mibilib
```

### Option B (Usage): Install with pip
This option is useful if you want this library to be installed as part of an
existing environment or as a dependency inside a requirements.txt file. You may
install a particular release using its tag (recommended)
```bash
pip install git+git://github.com/ionpath/mibilib@v1.2.8
```
or a branch (that may be under development with frequent changes)
```bash
pip install git+git://github.com/ionpath/master
```

## Usage
To use the MIBItracker API, you will need to use the backend url listed in the
About page which can be accessed after you have logged in from the menu
under your username in the upper right of the window.
```python
from mibitracker.request_helpers import MibiRequests

request = MibiRequests(
    'https://your-mibitracker-backend.appspot.com',
    'user@example.com',
    'password1234'
)
image_id = request.image_id('20180927', 'Point3')
image_details = request.get('/images/{}/'.format(image_id))
```

More examples can be found in the following notebooks:

 - [MIBItracker_API_Tutorial](MIBItracker_API_Tutorial.ipynb)

 - [MibiImage_Tutorial](MibiImage_Tutorial.ipynb)

 - [SingleCellSpatialExamples](SingleCellSpatialExamples.ipynb)

Full documentation for this library can be found at
https://ionpath.github.io/mibilib/.

## Sample data
Access to sample data to run the tutorials in the notebooks can be
requested by creating an account at the following URL:
https://mibi-share.ionpath.com.
