# mibilib-doc
Documentation for the mibilib package is available at
https://ionpath.github.io/mibilib/.

This directory contains the configuration for sphinx to auto-generate
the documentation.

It assumes the following directory structure:

```
mibilib/
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
parent mibilib directory:
```
sphinx-apidoc -f -o docs/source ./ */tests ./setup.py
sphinx-build -b html docs/source out
```
