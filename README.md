# datasette-edit-templates

<!-- [![PyPI](https://img.shields.io/pypi/v/datasette-edit-templates.svg)](https://pypi.org/project/datasette-edit-templates/)
[![Changelog](https://img.shields.io/github/v/release/simonw/datasette-edit-templates?include_prereleases&label=changelog)](https://github.com/simonw/datasette-edit-templates/releases) -->
[![Tests](https://github.com/simonw/datasette-edit-templates/workflows/Test/badge.svg)](https://github.com/simonw/datasette-edit-templates/actions?query=workflow%3ATest)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/simonw/datasette-edit-templates/blob/main/LICENSE)

Plugin allowing Datasette templates to be edited within Datasette.

**THIS PLUGIN IS CURRENTLY BROKEN - see [#1](https://github.com/simonw/datasette-edit-templates/issues/1) for details.**

<!--
## Installation

Install this plugin in the same environment as Datasette.

    $ datasette install datasette-edit-templates

## Usage

Usage instructions go here.
-->
## Development

To set up this plugin locally, first checkout the code. Then create a new virtual environment:

    cd datasette-edit-templates
    python3 -mvenv venv
    source venv/bin/activate

Or if you are using `pipenv`:

    pipenv shell

Now install the dependencies and tests:

    pip install -e '.[test]'

To run the tests:

    pytest
