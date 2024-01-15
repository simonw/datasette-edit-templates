from datasette.app import Datasette
import pytest_asyncio
import pytest
import sqlite_utils


@pytest.fixture
def db_path(tmpdir):
    db_path = str(tmpdir / "test.db")
    sqlite_utils.Database(db_path).vacuum()
    return db_path


@pytest.fixture
def db(db_path):
    return sqlite_utils.Database(db_path)


@pytest_asyncio.fixture
async def ds(db_path):
    ds = Datasette([db_path])
    await ds.invoke_startup()
    return ds


@pytest.mark.asyncio
async def test_loads_templates_on_startup(db_path, db):
    db["_templates_"].insert_all(
        [
            # Duplicated these with same created just to
            # make sure having exact same timestamp doesn't
            # crash the server on startup
            {
                "template": "_footer.html",
                "created": "2023-01-01T00:00:00",
                "body": "Hello world v2",
            },
            {
                "template": "_footer.html",
                "created": "2023-01-01T00:00:00",
                "body": "Hello world v2",
            },
            {
                "template": "_footer.html",
                "created": "2022-01-01T00:00:00",
                "body": "Hello world v1",
            },
        ]
    )
    ds = Datasette([db_path])
    await ds.invoke_startup()
    assert ds._edit_templates == {"_footer.html": "Hello world v2"}


@pytest.mark.asyncio
async def test_menu_link(ds):
    response = await ds.client.get("/")
    assert response.status_code == 200
    assert "Edit templates" not in response.text
    response = await ds.client.get(
        "/", cookies={"ds_actor": ds.sign({"a": {"id": "root"}}, "actor")}
    )
    assert response.status_code == 200
    assert "Edit templates" in response.text


@pytest.mark.asyncio
async def test_edit_template(ds, db):
    assert ds._edit_templates == {}
    actor = ds.sign({"a": {"id": "root"}}, "actor")
    response1 = await ds.client.get(
        "/-/edit-templates/_footer.html", cookies={"ds_actor": actor}
    )
    assert "New footer" not in response1.text
    assert response1.status_code == 200
    # Get CSRF cookie
    csrftoken = response1.cookies["ds_csrftoken"]
    response2 = await ds.client.post(
        "/-/edit-templates/_footer.html",
        cookies={"ds_actor": actor, "ds_csrftoken": csrftoken},
        data={"body": "New footer", "csrftoken": csrftoken},
    )
    assert ds._edit_templates == {"_footer.html": "New footer"}
    assert response2.status_code == 302
    assert response2.headers["Location"] == "/-/edit-templates/_footer.html"
    response3 = await ds.client.get("/")
    assert "New footer" in response3.text


@pytest.mark.asyncio
async def test_edit_template_permission_denied(ds):
    for path in ("/-/edit-templates/_footer.html", "/-/edit-templates"):
        response = await ds.client.get(path)
        assert response.status_code == 403
        assert "Permission denied" in response.text
