"""Setup file for installing dependencies for mibilib.

Copyright (C) 2021 Ionpath, Inc.  All rights reserved."""

from setuptools import setup

setup(name='mibilib',
      author='IONpath, Inc.',
      author_email='support@ionpath.com',
      version='1.4.3',
      url='https://github.com/ionpath/mibilib',
      description='Python utilities for IONpath MIBItracker and MIBItiff data',
      license='GNU General Public License v3.0',
      python_requires='~=3.7.3',
      install_requires=[
          'matplotlib==3.3.2',
          'numpy==1.20.0',
          'pandas==1.2.3',
          'pillow==9.0.1',
          'requests>=2.20.1',
          'scikit-image==0.18.0',
          'scikit-learn==0.23.2',
          'tifffile==2021.4.8',
          'tqdm==4.31.1',
      ],
      packages=['mibitracker', 'mibidata']
     )
