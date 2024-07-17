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
      python_requires='~=3.12.0',
      install_requires=[
          'matplotlib>=3.9.0',
          'numpy<2.0.0',
          'pandas>=2.2.0',
          'pillow>=10.4.0',
          'requests>=2.28.1',
          'scikit-image>=0.24.0',
          'scikit-learn>=1.5.0',
          'tifffile<2024.6.18',
          'tqdm>=4.66.0',
      ],
      packages=['mibitracker', 'mibidata']
     )
