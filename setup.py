"""Setup file for installing dependencies for MIBItracker-Client

Copyright (C) 2019 Ionpath, Inc.  All rights reserved."""

from setuptools import setup

setup(name='mibitracker-client',
      author='IONpath, Inc.',
      author_email='mibitracker-support@ionpath.com',
      version='1.0',
      url='https://github.com/ionpath/mibitracker-client',
      description='Python client and utilities for IONpath MIBItracker',
      license='GNU General Public License v3.0',
      python_requires='==3.6.*',
      install_requires=[
          'numpy==1.13.1',
          'pip==18.0',
          'requests==2.20.1',
          'scikit-image==0.13.0',
      ],
      packages=['mibitracker', 'mibidata']
     )
