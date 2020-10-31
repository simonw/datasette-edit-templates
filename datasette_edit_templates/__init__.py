from datasette import hookimpl
from datasette.utils.asgi import Response
import datetime

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
DEFAULT_SQL = "SELECT body FROM {} WHERE template = :template ORDER BY created DESC LIMIT 1".format(TABLE)
WRITE_SQL = "INSERT INTO {} (template, created, body) VALUES (:template, :created, :body)".format(
    TABLE
)


@hookimpl
def startup(datasette):
    async def inner():
        db = get_database(datasette)
        # Does the table exist?
        if not await db.table_exists(TABLE):
            for sql in CREATE_TABLE:
                await db.execute_write(sql, block=True)

    return inner


@hookimpl
def menu_links(datasette, actor):
    if actor and actor.get("id") == "root":
        return [
            {
                "href": datasette.urls.path("/-/edit-templates"),
                "label": "Edit templates",
            },
        ]


def get_database(datasette):
    plugin_config = datasette.plugin_config("datasette-edit-templates") or {}
    return datasette.get_database(plugin_config.get("database"))


@hookimpl
def load_template(template, datasette):
    async def inner():
        db = get_database(datasette)
        # Does it have a _templates_ table?
        if not await db.table_exists("_templates_"):
            return None
        # Does this template exist?
        results = await db.execute(DEFAULT_SQL, {"template": template})
        row = results.first()
        if row:
            return row[0]

    return inner


async def edit_templates_index(request, datasette):
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
        return Response.redirect(request.path)

    from_db = False
    row = (await db.execute(DEFAULT_SQL, {"template": template})).first()
    if row is None:
        # Load it from disk instead
        template_obj = datasette.jinja_env.get_template(template)
        import pdb; pdb.set_trace()
        # Load it from disk
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
