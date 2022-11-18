from datasette import hookimpl
from jinja2 import FunctionLoader
from datasette.utils.asgi import Response, Forbidden
import datetime
import inspect

TABLE = "_templates_"
CREATE_TABLE = [
    """
    CREATE TABLE {table} (
        [id] INTEGER PRIMARY KEY,
        [template] TEXT,
        [created] TEXT,
        [body] TEXT
    );""".format(
        table=TABLE
    ),
    """
    CREATE INDEX idx_template_created ON {table}(template, created);
    """.format(
        table=TABLE
    ),
]
DEFAULT_SQL = "SELECT body FROM {} WHERE template = :template ORDER BY created DESC LIMIT 1".format(
    TABLE
)
WRITE_SQL = "INSERT INTO {} (template, created, body) VALUES (:template, :created, :body)".format(
    TABLE
)


@hookimpl
def startup(datasette):
    datasette._edit_templates = {}

    async def inner():
        db = get_database(datasette)
        # Does the table exist?
        if not await db.table_exists(TABLE):
            for sql in CREATE_TABLE:
                await db.execute_write(sql, block=True)
        else:
            # Load all templates from that table
            rows = await db.execute("select template, body FROM {}".format(TABLE))
            for name, content in rows:
                datasette._edit_templates[name] = content

    return inner


@hookimpl
def permission_allowed(actor, action):
    if action == "edit-templates" and actor and actor.get("id") == "root":
        return True


@hookimpl
def menu_links(datasette, actor):
    async def inner():
        if not await datasette.permission_allowed(
            actor, "edit-templates", default=False
        ):
            return
        return [
            {
                "href": datasette.urls.path("/-/edit-templates"),
                "label": "Edit templates",
            },
        ]

    return inner


def get_database(datasette):
    plugin_config = datasette.plugin_config("datasette-edit-templates") or {}
    return datasette.get_database(plugin_config.get("database"))


class MyFunctionLoader(FunctionLoader):
    def list_templates(self):
        return []


@hookimpl
def prepare_jinja2_environment(env, datasette):
    def load_func(path):
        try:
            code = datasette._edit_templates[path]
            return code, path, lambda: True
        except KeyError:
            return None

    env.loader.loaders.insert(0, MyFunctionLoader(load_func))


async def edit_templates_index(request, datasette):
    if not await datasette.permission_allowed(
        request.actor, "edit-templates", default=False
    ):
        raise Forbidden("Permission denied for edit-templates")
    # Offer edit options for all disk templates
    return Response.html(
        await datasette.render_template(
            "edit_templates_index.html",
            {
                "templates": [
                    {"name": t, "default": True}
                    for t in datasette.jinja_env.list_templates()
                    if not t.startswith("default:")
                ]
            },
        )
    )


async def edit_template(request, datasette):
    if not await datasette.permission_allowed(
        request.actor, "edit-templates", default=False
    ):
        raise Forbidden("Permission denied for edit-templates")
    template = request.url_vars["template"]
    db = get_database(datasette)
    if request.method == "POST":
        post = await request.post_vars()
        body = post["body"]
        await db.execute_write(
            WRITE_SQL,
            {
                "template": template,
                "created": datetime.datetime.utcnow().isoformat(),
                "body": body,
            },
            block=True,
        )
        datasette.add_message(request, "Template changes saved")
        # Update the in-memory cache too
        datasette._edit_templates[template] = body
        # Clear the Jinja template cache so it sees the change
        datasette.jinja_env.cache.clear()
        return Response.redirect(request.path)

    from_db = False
    row = (await db.execute(DEFAULT_SQL, {"template": template})).first()
    if row is None:
        # Load it from disk instead
        template_obj = datasette.jinja_env.get_template(template)
        body = open(template_obj.filename).read()
        from_db = True
    else:
        body = row[0]
    return Response.html(
        await datasette.render_template(
            "edit_template.html",
            {
                "body": body,
                "template": template,
                "path": request.path,
                "from_db": from_db,
            },
            request=request,
        )
    )


@hookimpl
def register_routes():
    return [
        (r"^/-/edit-templates$", edit_templates_index),
        (r"^/-/edit-templates/(?P<template>.*)$", edit_template),
    ]
