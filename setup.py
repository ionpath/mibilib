"""Setup file for installing dependencies for MIBItracker-Client"""

from setuptools import setup

setup(name='MIBItrackerClient',
      version='1.0',
      url='https://github.com/ionpath/mibitracker-client',
      description='Python client for IONpath MIBItracker API.',
      license='GNU General Public License v3.0',
      install_requires=[
          'pip==18.0',
          'requests==2.14.2'
    ]
)