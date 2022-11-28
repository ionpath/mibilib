"""Setup file for installing dependencies for mibilib.

Copyright (C) 2022 Ionpath, Inc.  All rights reserved."""

from setuptools import setup

setup(name='mibilib',
      author='IONpath, Inc.',
      author_email='support@ionpath.com',
      version='1.5.0',
      url='https://github.com/ionpath/mibilib',
      description='Python utilities for IONpath MIBItracker and MIBItiff data',
      license='GNU General Public License v3.0',
      python_requires='~=3.11.0',
      install_requires=[
          'matplotlib==3.6.2',
          'numpy==1.23.5',
          'pandas==1.2.3',
          'pillow==9.3.0',
          'requests>=2.28.1',
          'scikit-image==0.19.3',
          'scikit-learn==1.1.3',
          'tifffile==2022.10.10',
          'tqdm==4.64.1',
      ],
      packages=['mibitracker', 'mibidata']
     )
