"""Module for replacing encoded entities in HTML."""

import re
from html import unescape

from djlint.settings import Config


def replace_html_escaped_entities(html: str, config: Config) -> str:
    """Replace encoded entities in HTML.

    Args:
    ----
        html (str): The HTML string to process.
        config (Config): The configuration object.

    Returns:
    -------
        str: The processed HTML string.
    """

    def replacement(match):
        return unescape(match.group())

    return re.sub(
        pattern=re.compile(
            pattern=r"&(?!(lt|gt|amp|quot|nbsp|ensp|emsp|thinsp))[#0-9a-z]{,30};",
            flags=re.IGNORECASE | re.DOTALL,
        ),
        repl=replacement,
        string=html,
    )
