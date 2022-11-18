from setuptools import setup
import os

VERSION = "0.2"


def get_long_description():
    with open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md"),
        encoding="utf8",
    ) as fp:
        return fp.read()


setup(
    name="datasette-edit-templates",
    description="Plugin allowing Datasette templates to be edited within Datasette",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Simon Willison",
    url="https://github.com/simonw/datasette-edit-templates",
    project_urls={
        "Issues": "https://github.com/simonw/datasette-edit-templates/issues",
        "CI": "https://github.com/simonw/datasette-edit-templates/actions",
        "Changelog": "https://github.com/simonw/datasette-edit-templates/releases",
    },
    license="Apache License, Version 2.0",
    version=VERSION,
    packages=["datasette_edit_templates"],
    entry_points={"datasette": ["edit_templates = datasette_edit_templates"]},
    install_requires=["datasette>=0.63"],
    package_data={
        "datasette_edit_templates": [
            "static/*.js",
            "templates/*.html",
        ],
    },
    extras_require={"test": ["pytest", "pytest-asyncio", "sqlite-utils"]},
    tests_require=["datasette-edit-templates[test]"],
    python_requires=">=3.7",
)
