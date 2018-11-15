"""Setup file for installing dependencies for MIBItracker-Client

Copyright (C) 2018 Ionpath, Inc.  All rights reserved."""

from setuptools import setup

setup(name='mibitracker-client',
      author='IONpath, Inc.',
      author_email='mibitracker-support@ionpath.com',
      version='1.0',
      url='https://github.com/ionpath/mibitracker-client',
      description='Python client for IONpath MIBItracker API.',
      license='GNU General Public License v3.0',
      python_requires='==3.6.*',
      install_requires=[
          'pip==18.0',
          'requests==2.14.2'
      ],
      packages=['mibitracker', 'mibitof']
     )
