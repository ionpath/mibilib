"""Setup file for installing dependencies for MIBItracker-Client

Copyright (C) 2019 Ionpath, Inc.  All rights reserved."""

from setuptools import setup

setup(name='mibitracker-client',
      author='IONpath, Inc.',
      author_email='mibitracker-support@ionpath.com',
      version='1.2.9',
      url='https://github.com/ionpath/mibitracker-client',
      description='Python utilities for IONpath MIBItracker and MIBItiff data',
      license='GNU General Public License v3.0',
      python_requires='~=3.6',
      install_requires=[
          'matplotlib==2.2.3',
          'numpy==1.16.0',
          'pandas==0.23.4',
          'pillow==6.2.2',
          'pip==19.1.1',
          'requests==2.20.1',
          'scikit-image==0.14.2',
          'scikit-learn==0.20.3',
          'tqdm==4.31.1',
      ],
      packages=['mibitracker', 'mibidata']
     )
