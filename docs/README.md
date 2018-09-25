# mibitracker-client-doc
Documentation for the mibitracker-client package is available at
https://ionpath.github.io/mibitracker-client/.

This directory contains the configuration for sphinx to auto-generate
the documentation.

It assumes the following directory structure:

```
mibitracker-client/
|-- README
|-- setup.py
`-- mibitracker/
    |-- __init__.py
    |-- submodule1.py
    |-- submodule2.py
    `-- tests/
docs/
    |-- MakeFile
    `-- source/
```

To generated updated .rst files in the source/ directory, and a build/
directory containing the .html docs, execute the following commands from the
parent mibitracker-client directory:
```
sphinx-apidoc -f -o docs/source ./mibitracker ./mibitracker/{**,}/tests
make -C docs/ html
```
