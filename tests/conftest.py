import datasette
from datasette_test import wait_until_responds
import pytest
import sqlite_utils
from subprocess import Popen, PIPE
import sys


def pytest_report_header():
    return "Datasette: {}".format(datasette.__version__)


@pytest.fixture(scope="session")
def ds_server(tmp_path_factory):
    tmpdir = tmp_path_factory.mktemp("tmp")
    db_path = str(tmpdir / "data.db")
    db = sqlite_utils.Database(db_path)
    db["animals"].insert({"id": 1, "name": "Panda"}, pk="id")
    process = Popen(
        [
            sys.executable,
            "-m",
            "datasette",
            "--port",
            "8126",
            str(db_path),
            "--secret",
            "1",
        ],
        stdout=PIPE,
    )
    wait_until_responds("http://localhost:8126/")
    yield "http://localhost:8126"
    process.terminate()
    process.wait()
