from jinja2 import Environment, PackageLoader

jinja_env = Environment(
    loader=PackageLoader("clarity_epp", "templates"),
    autoescape=False,  # text files, not HTML
    keep_trailing_newline=True,
    trim_blocks=True,  # Remove the first newline after a block tag.
    lstrip_blocks=True,  # Remove spaces and tabs before block tags.
)


def render_template(template_name: str, **kwargs: dict) -> str:
    """Render a template with the given name and keyword arguments.

    Args:
        template_name: The name of the template to render.
        **kwargs: The keyword arguments to pass to the template.

    Returns:
        The rendered template as a string.

    """
    template = jinja_env.get_template(template_name)
    return template.render(**kwargs)
