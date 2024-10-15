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
      python_requires='>=3.8',
      install_requires=[
          'matplotlib>=3.6',
          'numpy<2.0',
          'pandas>=1.0',
          'pillow>=9.0',
          'requests>=2.28',
          'scikit-image>=0.19',
          'scikit-learn>=1.1',
          'tifffile<2024.6.18',
          'tqdm>=4.64',
      ],
      packages=['mibitracker', 'mibidata']
     )
