# datasette-edit-templates

[![PyPI](https://img.shields.io/pypi/v/datasette-edit-templates.svg)](https://pypi.org/project/datasette-edit-templates/)
[![Changelog](https://img.shields.io/github/v/release/simonw/datasette-edit-templates?include_prereleases&label=changelog)](https://github.com/simonw/datasette-edit-templates/releases)
[![Tests](https://github.com/simonw/datasette-edit-templates/workflows/Test/badge.svg)](https://github.com/simonw/datasette-edit-templates/actions?query=workflow%3ATest)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/simonw/datasette-edit-templates/blob/main/LICENSE)

Plugin allowing Datasette templates to be edited within Datasette.

## Installation

Install this plugin in the same environment as Datasette.

    $ datasette install datasette-edit-templates

## Usage

On startup. a `_templates_` table will be created in the database you are running Datasette against.

Use the app menu to navigate to the `/-/edit-templates` page, and edit templates there.

Changes should become visible instantly, and will be persisted to your database.

The interface is only available to users with the `edit-templates` permission.

The `root` user is granted this permission by default. You can sign in as the root user using `datasette mydb.db --root`.

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
