[![CircleCI](https://circleci.com/gh/ionpath/mibitracker-client.svg?style=svg&circle-token=e798611a4abf9f2503a532c8ad5fd02d849d85a0)](https://circleci.com/gh/ionpath/mibitracker-client)

# mibitracker-client

Python client for IONpath MIBItracker API, plus utility functions for working
with MIBItiff images.

https://ionpath.github.io/mibitracker-client/

## Setup

### Install Python 3.6
Install the Python 3.6 version of [Miniconda](https://conda.io/miniconda.html).
Even if your system already has a version of Python installed, it is strongly
recommended to use the `conda` environment manager to install and manage this
library's dependencies.

### Option A: Clone repository and create environement
This option downloads the source code and creates the development environment.
```bash
cd <path/to/where/you/want/to/install/project>
git clone https://github.com/ionpath/mibitracker-client
cd mibitracker-client
```

```bash
conda env create -f environment.yml
source activate mibitracker-client  # On Windows, omit the 'source' part
```

### Option B: Install with pip
This option is useful if you want this library to be installed as part of an
existing environment or as a dependency inside a requirements.txt file.
```
pip install git+git://github.com/ionpath/mibitracker-client@master
```

## Usage
```
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

Full documentation for this library can be found at
https://ionpath.github.io/mibitracker-client/.
