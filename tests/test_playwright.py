from datasette_test import Datasette
import pytest

try:
    from playwright import sync_api
except ImportError:
    sync_api = None

pytestmark = pytest.mark.skipif(sync_api is None, reason="playwright not installed")


@pytest.mark.parametrize("logged_in", (True, False))
def test_edit_template_page(ds_server, page, logged_in):
    if logged_in:
        ds = Datasette(secret="1")
        ds_actor = ds.sign({"a": {"id": "root"}}, "actor")
        page.context.add_cookies(
            [
                {
                    "name": "ds_actor",
                    "value": ds_actor,
                    "url": "http://localhost:8126",
                }
            ]
        )
    else:
        page.context.clear_cookies()

    responses = []
    console_errors = []

    def collect_errors(msg):
        if msg.type in ("error", "warning"):
            console_errors.append(msg.text)

    page.on("console", collect_errors)

    def handle_response(response):
        responses.append(response)

    page.on("response", handle_response)

    page.goto(ds_server + "/-/edit-templates/_footer.html")

    response = responses[0]

    if not logged_in:
        assert response.status == 403
    else:
        assert response.status == 200
        # Wait for CodeMirror to load
        page.wait_for_selector(".CodeMirror", timeout=2000)

        # Should not have seen any JS errors
        assert not console_errors, "\n".join(console_errors)
