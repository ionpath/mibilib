# mibitracker-client

Python client for IONpath MIBItracker API. Full documentation can be found at
https://ionpath.github.io/mibitracker-client/.

## Setup

### Install Python 3.6
Install the Python 3.6 version of [Miniconda](https://conda.io/miniconda.html).
Even if your system already has a version of Python installed, you will need
to use the `conda` environment manager to install and manage this
library's dependencies.

### Clone repository
```bash
cd <path/to/where/you/want/to/install/project>
git clone https://github.com/ionpath/mibitracker-client
```

### Create conda environment
```bash
conda env create -f environment.yml
source activate mibitracker-client  # On Windows, omit the 'source' part
```
