from datasette import hookimpl
from datasette.permissions import Action
from jinja2 import FunctionLoader, TemplateNotFound
from datasette.utils.asgi import Response, Forbidden
import datetime

TABLE = "_templates_"
CREATE_TABLE_SQLS = [
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
LOAD_TEMPLATE_SQL = """
select template, body
from {table}
group by template
having created = max(created)
""".format(
    table=TABLE
)
GET_TEMPLATE_SQL = "SELECT id, body FROM {} WHERE template = :template ORDER BY created DESC LIMIT 1".format(
    TABLE
)
WRITE_TEMPLATE_SQL = "INSERT INTO {} (template, created, body) VALUES (:template, :created, :body)".format(
    TABLE
)


def pretty_datetime(d):
    if d:
        return datetime.datetime.fromisoformat(d).strftime("%Y-%m-%d %H:%M:%S")
    else:
        return ""


def get_environment(datasette, request):
    if hasattr(datasette, "get_jinja_environment"):
        return datasette.get_jinja_environment(request)
    return datasette.jinja_env


@hookimpl
def startup(datasette):
    datasette._edit_templates = {}

    async def inner():
        db = get_database(datasette)
        # Does the table exist?
        if not await db.table_exists(TABLE):
            for sql in CREATE_TABLE_SQLS:
                await db.execute_write(sql, block=True)
        else:
            # Load all templates from that table
            rows = await db.execute(LOAD_TEMPLATE_SQL)
            for name, content in rows:
                datasette._edit_templates[name] = content

    return inner


@hookimpl
def register_actions():
    return (
        Action(
            name="edit-templates",
            description="Edit Datasette templates",
        ),
    )


@hookimpl
def menu_links(datasette, actor):
    config = datasette.plugin_config("datasette-edit-templates") or {}
    if "menu_label" not in config:
        menu_label = "Edit templates"
    else:
        menu_label = config.get("menu_label")
    if menu_label is None:
        return

    async def inner():
        if not await datasette.allowed(action="edit-templates", actor=actor):
            return
        return [
            {
                "href": datasette.urls.path("/-/edit-templates"),
                "label": menu_label,
            },
        ]

    return inner


def get_database(datasette):
    plugin_config = datasette.plugin_config("datasette-edit-templates") or {}
    if plugin_config.get("internal_db"):
        return datasette.get_internal_database()
    return datasette.get_database(plugin_config.get("database"))


class MyFunctionLoader(FunctionLoader):
    def list_templates(self):
        return []


@hookimpl
def prepare_jinja2_environment(env, datasette):
    config = datasette.plugin_config("datasette-edit-templates") or {}
    if config.get("skip_prepare_jinja2_environment"):
        return

    def load_func(path):
        try:
            code = datasette._edit_templates[path]
            return code, path, lambda: True
        except KeyError:
            return None

    env.loader.loaders.insert(0, MyFunctionLoader(load_func))


async def edit_templates_index(request, datasette):
    if not await datasette.allowed(
        action="edit-templates",
        actor=request.actor,
    ):
        raise Forbidden("Permission denied for edit-templates")
    template_name = request.args.get("template")
    if template_name:
        return Response.redirect(
            datasette.urls.path("/-/edit-templates/{}".format(template_name))
        )
    db = get_database(datasette)

    # List both templates from DB and default unedited templates
    templates = [
        dict(row)
        for row in await db.execute(
            """
            select template as name, max(created) as last_updated, count(*) as revisions
            from {} group by template order by created desc
            """.format(
                TABLE
            )
        )
    ]
    by_name = {t["name"]: t for t in templates}

    environment = get_environment(datasette, request)

    for template in environment.list_templates():
        if template.startswith("default:"):
            continue
        if template in by_name:
            pass
        else:
            templates.append(
                {
                    "name": template,
                    "last_edited": None,
                    "revisions": "",
                }
            )

    # Offer edit options for all disk templates
    return Response.html(
        await datasette.render_template(
            "edit_templates_index.html",
            {
                "templates": templates,
                "pretty_datetime": pretty_datetime,
            },
        )
    )


async def edit_template(request, datasette):
    if not await datasette.allowed(
        action="edit-templates",
        actor=request.actor,
    ):
        raise Forbidden("Permission denied for edit-templates")
    template = request.url_vars["template"]
    db = get_database(datasette)
    if request.method == "POST":
        post = await request.post_vars()
        body = post["body"]
        await db.execute_write(
            WRITE_TEMPLATE_SQL,
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
        get_environment(datasette, request).cache.clear()
        return Response.redirect(request.path)

    create_from_scratch = False
    row = (await db.execute(GET_TEMPLATE_SQL, {"template": template})).first()
    requested_revision = request.args.get("revision")
    revision = None
    if requested_revision:
        row = (
            await db.execute(
                "select id, created, body from {} where id = :id".format(TABLE),
                {"id": requested_revision},
            )
        ).first()
        revision = dict(row)
    revisions = []
    if row is None:
        from_db = False
        # Load it from disk instead
        try:
            environment = get_environment(datasette, request)
            template_obj = environment.get_template(template)
            body = open(template_obj.filename).read()
        except TemplateNotFound:
            body = ""
            create_from_scratch = True
    else:
        from_db = True
        body = row["body"]
        # And load revisions
        revisions = [
            dict(revision)
            for revision in (
                await db.execute(
                    "select id, created from {} where template = :template and id != :id order by created desc".format(
                        TABLE
                    ),
                    {"template": template, "id": row["id"]},
                )
            ).rows
        ]
    return Response.html(
        await datasette.render_template(
            "edit_template.html",
            {
                "body": body,
                "template": template,
                "revision": revision,
                "path": request.path,
                "from_db": from_db,
                "create_from_scratch": create_from_scratch,
                "revisions": revisions,
                "pretty_datetime": pretty_datetime,
            },
            request=request,
        )
    )


@hookimpl
def register_routes():
    return [
        (r"^/-/edit-templates$", edit_templates_index),
        (r"^/-/edit-templates/(?P<template>.+)$", edit_template),
    ]
